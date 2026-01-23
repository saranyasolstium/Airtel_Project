import cv2
import numpy as np
import requests
import base64
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import threading
from collections import deque
import argparse

# -------------------- Configuration --------------------


class Config:
    # RTSP URL - Update this with your camera URL
    RTSP_URL = "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101"

    # API Endpoint
    API_URL = "http://127.0.0.1:8000/api/crowd/alerts"

    # Crowd thresholds
    MAX_PERSON_COUNT = 10  # Alert when more than 10 people

    # Detection settings
    CONFIDENCE_THRESHOLD = 0.35
    NMS_THRESHOLD = 0.3
    PROCESS_EVERY_N_FRAMES = 2

    # Model paths (using YOLOv8 for person detection)
    MODEL_PATH = "yolov8n.pt"  # Will auto-download if not present

    # Zone configuration (points in polygon format)
    # Format: [[x1,y1], [x2,y2], [x3,y3], ...]
    ZONE_POINTS = [
        [100, 100],   # Top-left
        [500, 100],   # Top-right
        [500, 400],   # Bottom-right
        [100, 400]    # Bottom-left
    ]

    # Zone and camera names for API
    ZONE_NAME = "Main_Entrance"
    CAMERA_NAME = "Camera_01"

    # Alert cooldown (seconds) to avoid spam
    ALERT_COOLDOWN = 30

    # Save images for debugging
    SAVE_ALERT_IMAGES = True
    ALERT_IMAGES_DIR = "crowd_alerts"

    # Stream reconnection settings
    RECONNECT_DELAY = 5
    MAX_RECONNECT_ATTEMPTS = 10

# -------------------- YOLO Model Wrapper --------------------


class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Initialize YOLO model for person detection.

        Args:
            model_path: Path to YOLO model weights (.pt file)
        """
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            print(f"Loaded YOLO model from {model_path}")
        except ImportError:
            print(
                "Error: ultralytics not installed. Install with: pip install ultralytics")
            raise
        except Exception as e:
            print(f"Error loading model: {e}")
            # Try to download model
            try:
                from ultralytics import YOLO
                self.model = YOLO('yolov8n.pt')
                print("Downloaded YOLOv8n model")
            except Exception as e2:
                print(f"Failed to download model: {e2}")
                raise

    def detect_people(self, frame: np.ndarray, conf_threshold: float = 0.35) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect people in frame.

        Returns:
            List of bounding boxes [x1, y1, x2, y2, confidence]
        """
        if frame is None or frame.size == 0:
            return []

        try:
            # Run inference
            results = self.model(frame, verbose=False, conf=conf_threshold)

            people_boxes = []

            if results and len(results) > 0:
                boxes = results[0].boxes

                if boxes is not None:
                    # Get class IDs (0 = person in COCO dataset)
                    classes = boxes.cls.cpu().numpy() if boxes.cls is not None else []
                    confidences = boxes.conf.cpu().numpy() if boxes.conf is not None else []
                    xyxy = boxes.xyxy.cpu().numpy() if boxes.xyxy is not None else []

                    for i in range(len(classes)):
                        # Check if detection is a person (class 0)
                        if int(classes[i]) == 0:
                            x1, y1, x2, y2 = map(int, xyxy[i])
                            conf = float(confidences[i])
                            people_boxes.append((x1, y1, x2, y2, conf))

            return people_boxes

        except Exception as e:
            print(f"Detection error: {e}")
            return []

# -------------------- Zone Management --------------------


class ZoneManager:
    def __init__(self, zone_points: List[List[int]]):
        """
        Initialize zone with polygon points.

        Args:
            zone_points: List of [x,y] points defining polygon
        """
        self.zone_points = np.array(zone_points, np.int32)
        self.zone_polygon = self.zone_points.reshape((-1, 1, 2))

    def point_in_zone(self, x: int, y: int) -> bool:
        """Check if point is inside zone polygon."""
        return cv2.pointPolygonTest(self.zone_polygon, (float(x), float(y)), False) >= 0

    def count_people_in_zone(self, people_boxes: List[Tuple[int, int, int, int, float]]) -> int:
        """
        Count people whose center point is inside the zone.

        Args:
            people_boxes: List of bounding boxes [x1, y1, x2, y2, confidence]

        Returns:
            Number of people in zone
        """
        count = 0
        for (x1, y1, x2, y2, conf) in people_boxes:
            # Calculate center of bounding box
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            if self.point_in_zone(cx, cy):
                count += 1

        return count

    def draw_zone(self, frame: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0),
                  thickness: int = 2, fill_alpha: float = 0.1) -> np.ndarray:
        """Draw zone polygon on frame."""
        overlay = frame.copy()

        # Draw filled polygon
        cv2.fillPoly(overlay, [self.zone_points], color)

        # Blend with original
        frame = cv2.addWeighted(overlay, fill_alpha, frame, 1 - fill_alpha, 0)

        # Draw polygon outline
        cv2.polylines(frame, [self.zone_points], True, color, thickness)

        return frame

# -------------------- Alert Manager --------------------


class AlertManager:
    def __init__(self, api_url: str, zone_name: str, camera_name: str, max_person_count: int = 10):
        self.api_url = api_url
        self.zone_name = zone_name
        self.camera_name = camera_name
        self.max_person_count = max_person_count
        self.last_alert_time = 0
        self.alert_cooldown = Config.ALERT_COOLDOWN

        # Create directory for alert images if needed
        if Config.SAVE_ALERT_IMAGES:
            os.makedirs(Config.ALERT_IMAGES_DIR, exist_ok=True)

    def should_send_alert(self) -> bool:
        """Check if enough time has passed since last alert."""
        current_time = time.time()
        return (current_time - self.last_alert_time) >= self.alert_cooldown

    def frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert OpenCV frame to base64 string."""
        if frame is None or frame.size == 0:
            return ""

        try:
            # Encode frame as JPEG
            success, encoded_image = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if success:
                # Convert to base64
                base64_string = base64.b64encode(encoded_image).decode('utf-8')
                return base64_string
            else:
                print("Failed to encode image")
                return ""
        except Exception as e:
            print(f"Error converting frame to base64: {e}")
            return ""

    def save_alert_image(self, frame: np.ndarray, person_count: int) -> Optional[str]:
        """Save alert image to disk for debugging."""
        if not Config.SAVE_ALERT_IMAGES:
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alert_{self.zone_name}_{timestamp}_{person_count}people.jpg"
            filepath = os.path.join(Config.ALERT_IMAGES_DIR, filename)

            # Draw alert text on image
            alert_frame = frame.copy()

            # Draw red border
            cv2.rectangle(alert_frame, (0, 0), (alert_frame.shape[1], alert_frame.shape[0]),
                          (0, 0, 255), 10)

            # Add text overlay
            text = f"ALERT: {person_count} people (Threshold: {self.max_person_count})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.0
            thickness = 2

            # Calculate text size
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = (alert_frame.shape[1] - text_size[0]) // 2
            text_y = 50

            # Draw text background
            cv2.rectangle(alert_frame,
                          (text_x - 10, text_y - text_size[1] - 10),
                          (text_x + text_size[0] + 10, text_y + 10),
                          (0, 0, 0), -1)

            # Draw text
            cv2.putText(alert_frame, text, (text_x, text_y),
                        font, font_scale, (0, 0, 255), thickness)

            # Save image
            cv2.imwrite(filepath, alert_frame)
            print(f"Saved alert image to: {filepath}")

            return filepath

        except Exception as e:
            print(f"Error saving alert image: {e}")
            return None

    def send_alert(self, frame: np.ndarray, person_count: int) -> bool:
        """
        Send crowd alert to API.

        Args:
            frame: OpenCV frame containing the crowd
            person_count: Number of people detected in zone

        Returns:
            True if alert sent successfully, False otherwise
        """
        if not self.should_send_alert():
            print(f"Alert cooldown active. Skipping alert.")
            return False

        try:
            # Convert frame to base64
            image_base64 = self.frame_to_base64(frame)
            if not image_base64:
                print("Failed to convert frame to base64")
                return False

            # Prepare payload
            payload = {
                "zone_name": self.zone_name,
                "camera_name": self.camera_name,
                "person_count": person_count,
                "image_base64": image_base64,
                "max_count": self.max_person_count
            }

            print(f"Sending alert to {self.api_url}")
            print(f"Payload: zone={self.zone_name}, camera={self.camera_name}, "
                  f"count={person_count}, max={self.max_person_count}")

            # Send POST request
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            # Check response
            if response.status_code == 200:
                print(
                    f"Alert sent successfully! Response: {response.text[:100]}")
                self.last_alert_time = time.time()

                # Save alert image for debugging
                if Config.SAVE_ALERT_IMAGES:
                    self.save_alert_image(frame, person_count)

                return True
            else:
                print(
                    f"Failed to send alert. Status: {response.status_code}, Response: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"Connection error: Cannot connect to API at {self.api_url}")
            return False
        except requests.exceptions.Timeout:
            print("Request timeout")
            return False
        except Exception as e:
            print(f"Error sending alert: {e}")
            return False

# -------------------- Video Stream Manager --------------------


class VideoStreamManager:
    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.frame_width = 0
        self.frame_height = 0
        self.reconnect_attempts = 0

    def connect(self) -> bool:
        """Connect to RTSP stream."""
        try:
            print(f"Connecting to RTSP stream: {self.rtsp_url}")
            self.cap = cv2.VideoCapture(self.rtsp_url)

            # Set buffer size
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Try to get a frame to verify connection
            ret, frame = self.cap.read()

            if ret and frame is not None:
                self.frame_height, self.frame_width = frame.shape[:2]
                print(
                    f"Connected successfully. Resolution: {self.frame_width}x{self.frame_height}")
                self.reconnect_attempts = 0
                return True
            else:
                print("Failed to read frame from stream")
                self.disconnect()
                return False

        except Exception as e:
            print(f"Error connecting to stream: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect from stream."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def reconnect(self) -> bool:
        """Attempt to reconnect to stream."""
        if self.reconnect_attempts >= Config.MAX_RECONNECT_ATTEMPTS:
            print(
                f"Max reconnection attempts ({Config.MAX_RECONNECT_ATTEMPTS}) reached")
            return False

        self.reconnect_attempts += 1
        print(
            f"Reconnection attempt {self.reconnect_attempts}/{Config.MAX_RECONNECT_ATTEMPTS}")

        self.disconnect()
        time.sleep(Config.RECONNECT_DELAY)

        return self.connect()

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the stream."""
        if self.cap is None or not self.cap.isOpened():
            print("Stream not connected")
            return None

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("Failed to read frame")
                return None

            return frame

        except Exception as e:
            print(f"Error reading frame: {e}")
            return None

# -------------------- Crowd Detection System --------------------


class CrowdDetectionSystem:
    def __init__(self):
        # Initialize components
        self.video_manager = VideoStreamManager(Config.RTSP_URL)
        self.detector = YOLODetector(Config.MODEL_PATH)
        self.zone_manager = ZoneManager(Config.ZONE_POINTS)
        self.alert_manager = AlertManager(
            api_url=Config.API_URL,
            zone_name=Config.ZONE_NAME,
            camera_name=Config.CAMERA_NAME,
            max_person_count=Config.MAX_PERSON_COUNT
        )

        # Statistics
        self.frame_count = 0
        self.person_count_history = deque(maxlen=100)  # Store last 100 counts
        self.alert_count = 0
        self.start_time = time.time()

        # Control flags
        self.running = False
        self.paused = False

        # Display window name
        self.window_name = "Crowd Detection System"

    def draw_detections(self, frame: np.ndarray, people_boxes: List[Tuple[int, int, int, int, float]],
                        people_in_zone: int) -> np.ndarray:
        """Draw detections and information on frame."""
        if frame is None:
            return frame

        display_frame = frame.copy()

        # Draw zone
        display_frame = self.zone_manager.draw_zone(display_frame)

        # Draw all people detections
        for (x1, y1, x2, y2, conf) in people_boxes:
            # Calculate center point
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # Check if in zone
            in_zone = self.zone_manager.point_in_zone(cx, cy)

            # Choose color based on zone status
            # Green for in zone, Blue for outside
            color = (0, 255, 0) if in_zone else (255, 0, 0)

            # Draw bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)

            # Draw center point
            cv2.circle(display_frame, (cx, cy), 3, color, -1)

            # Draw confidence
            label = f"Person: {conf:.2f}"
            label_size, base_line = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            y1_label = max(y1, label_size[1] + 10)
            cv2.rectangle(display_frame, (x1, y1_label - label_size[1] - 10),
                          (x1 + label_size[0], y1_label), color, -1)
            cv2.putText(display_frame, label, (x1, y1_label - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Add info overlay
        info_texts = [
            f"Zone: {Config.ZONE_NAME}",
            f"Camera: {Config.CAMERA_NAME}",
            f"People in zone: {people_in_zone}/{Config.MAX_PERSON_COUNT}",
            f"Total detections: {len(people_boxes)}",
            f"Alerts sent: {self.alert_count}",
            f"FPS: {self.get_fps():.1f}"
        ]

        # Draw semi-transparent background for text
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 10 +
                      len(info_texts) * 30 + 10), (0, 0, 0), -1)
        display_frame = cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0)

        # Draw texts
        for i, text in enumerate(info_texts):
            y_pos = 40 + i * 30
            color = (0, 255, 0) if i == 2 and people_in_zone < Config.MAX_PERSON_COUNT else (
                0, 0, 255) if i == 2 else (255, 255, 255)
            cv2.putText(display_frame, text, (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Draw alert status
        if people_in_zone >= Config.MAX_PERSON_COUNT:
            alert_text = f"ALERT: Crowd limit exceeded!"
            text_size = cv2.getTextSize(
                alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)[0]
            text_x = (display_frame.shape[1] - text_size[0]) // 2
            text_y = display_frame.shape[0] - 50

            # Draw alert background
            cv2.rectangle(display_frame, (text_x - 10, text_y - text_size[1] - 10),
                          (text_x + text_size[0] + 10, text_y + 10), (0, 0, 0), -1)

            # Draw alert text
            cv2.putText(display_frame, alert_text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        return display_frame

    def get_fps(self) -> float:
        """Calculate current FPS."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.frame_count / elapsed
        return 0.0

    def update_statistics(self, people_in_zone: int):
        """Update statistics and check for alerts."""
        self.person_count_history.append(people_in_zone)

        # Check if crowd threshold is exceeded
        if people_in_zone >= Config.MAX_PERSON_COUNT:
            print(
                f"Crowd alert! {people_in_zone} people in zone (threshold: {Config.MAX_PERSON_COUNT})")

    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process a single frame for crowd detection."""
        if frame is None or frame.size == 0:
            return None

        self.frame_count += 1

        # Process every N frames for performance
        if self.frame_count % Config.PROCESS_EVERY_N_FRAMES != 0:
            return frame

        # Detect people
        people_boxes = self.detector.detect_people(
            frame, Config.CONFIDENCE_THRESHOLD)

        # Count people in zone
        people_in_zone = self.zone_manager.count_people_in_zone(people_boxes)

        # Update statistics
        self.update_statistics(people_in_zone)

        # Check and send alert if needed
        if people_in_zone >= Config.MAX_PERSON_COUNT:
            # Send alert
            if self.alert_manager.send_alert(frame, people_in_zone):
                self.alert_count += 1

        # Draw detections on frame for display
        display_frame = self.draw_detections(
            frame, people_boxes, people_in_zone)

        return display_frame

    def run(self):
        """Main loop for crowd detection system."""
        print("Starting Crowd Detection System...")
        print(f"Zone: {Config.ZONE_NAME}")
        print(f"Camera: {Config.CAMERA_NAME}")
        print(f"Crowd threshold: {Config.MAX_PERSON_COUNT} people")
        print(f"Zone points: {Config.ZONE_POINTS}")
        print("Press 'q' to quit, 'p' to pause, 'r' to reset statistics")
        print("-" * 50)

        # Connect to stream
        if not self.video_manager.connect():
            print("Failed to connect to video stream")
            return

        self.running = True

        try:
            while self.running:
                if not self.paused:
                    # Read frame
                    frame = self.video_manager.read_frame()

                    if frame is None:
                        print("Failed to read frame. Attempting to reconnect...")
                        if not self.video_manager.reconnect():
                            print("Reconnection failed. Exiting...")
                            break
                        continue

                    # Process frame
                    processed_frame = self.process_frame(frame)

                    if processed_frame is not None:
                        # Display frame
                        cv2.imshow(self.window_name, processed_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    print("Quitting...")
                    self.running = False
                elif key == ord('p'):
                    self.paused = not self.paused
                    print(f"System {'paused' if self.paused else 'resumed'}")
                elif key == ord('r'):
                    self.alert_count = 0
                    self.frame_count = 0
                    self.start_time = time.time()
                    self.person_count_history.clear()
                    print("Statistics reset")
                elif key == ord('s'):
                    # Save current frame
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"snapshot_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"Snapshot saved: {filename}")

        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources."""
        print("\nCleaning up...")
        self.running = False

        # Close video stream
        self.video_manager.disconnect()

        # Close display window
        cv2.destroyAllWindows()

        # Print final statistics
        print("\n" + "=" * 50)
        print("FINAL STATISTICS")
        print("=" * 50)
        print(f"Total frames processed: {self.frame_count}")
        print(f"Total alerts sent: {self.alert_count}")
        print(f"Average FPS: {self.get_fps():.1f}")
        if self.person_count_history:
            avg_people = sum(self.person_count_history) / \
                len(self.person_count_history)
            max_people = max(self.person_count_history)
            print(f"Average people in zone: {avg_people:.1f}")
            print(f"Maximum people in zone: {max_people}")
        print("=" * 50)

# -------------------- Configuration Update Functions --------------------


def update_config_from_file(config_file: str = "crowd_config.json"):
    """Update configuration from JSON file."""
    if not os.path.exists(config_file):
        print(
            f"Config file {config_file} not found. Using default configuration.")
        return

    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Update configuration
        if 'RTSP_URL' in config_data:
            Config.RTSP_URL = config_data['RTSP_URL']
            print(f"Updated RTSP_URL: {Config.RTSP_URL}")

        if 'API_URL' in config_data:
            Config.API_URL = config_data['API_URL']
            print(f"Updated API_URL: {Config.API_URL}")

        if 'MAX_PERSON_COUNT' in config_data:
            Config.MAX_PERSON_COUNT = config_data['MAX_PERSON_COUNT']
            print(f"Updated MAX_PERSON_COUNT: {Config.MAX_PERSON_COUNT}")

        if 'ZONE_POINTS' in config_data:
            Config.ZONE_POINTS = config_data['ZONE_POINTS']
            print(f"Updated ZONE_POINTS: {Config.ZONE_POINTS}")

        if 'ZONE_NAME' in config_data:
            Config.ZONE_NAME = config_data['ZONE_NAME']
            print(f"Updated ZONE_NAME: {Config.ZONE_NAME}")

        if 'CAMERA_NAME' in config_data:
            Config.CAMERA_NAME = config_data['CAMERA_NAME']
            print(f"Updated CAMERA_NAME: {Config.CAMERA_NAME}")

        print("Configuration updated from file.")

    except Exception as e:
        print(f"Error loading config file: {e}")


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "RTSP_URL": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
        "API_URL": "http://127.0.0.1:8000/api/crowd/alerts",
        "MAX_PERSON_COUNT": 10,
        "ZONE_POINTS": [
            [100, 100],
            [500, 100],
            [500, 400],
            [100, 400]
        ],
        "ZONE_NAME": "Main_Entrance",
        "CAMERA_NAME": "Camera_01",
        "CONFIDENCE_THRESHOLD": 0.35,
        "PROCESS_EVERY_N_FRAMES": 2,
        "ALERT_COOLDOWN": 30
    }

    with open("crowd_config_sample.json", 'w') as f:
        json.dump(sample_config, f, indent=4)

    print("Sample configuration file created: crowd_config_sample.json")
    print("Copy it to 'crowd_config.json' and modify as needed.")

# -------------------- Main Function --------------------


def main():
    parser = argparse.ArgumentParser(
        description="Crowd Formation Alert System")
    parser.add_argument("--config", type=str, default="crowd_config.json",
                        help="Path to configuration JSON file")
    parser.add_argument("--create-sample", action="store_true",
                        help="Create a sample configuration file")
    parser.add_argument("--rtsp", type=str, help="RTSP URL for camera stream")
    parser.add_argument("--api", type=str, help="API endpoint URL")
    parser.add_argument("--zone", type=str, help="Zone name")
    parser.add_argument("--camera", type=str, help="Camera name")
    parser.add_argument("--threshold", type=int,
                        help="Crowd threshold (number of people)")
    parser.add_argument("--zone-points", type=str,
                        help="Zone points as JSON string")

    args = parser.parse_args()

    # Create sample config if requested
    if args.create_sample:
        create_sample_config()
        return

    # Update configuration from file
    update_config_from_file(args.config)

    # Override with command line arguments
    if args.rtsp:
        Config.RTSP_URL = args.rtsp
        print(f"Using RTSP URL from command line: {Config.RTSP_URL}")

    if args.api:
        Config.API_URL = args.api
        print(f"Using API URL from command line: {Config.API_URL}")

    if args.zone:
        Config.ZONE_NAME = args.zone
        print(f"Using zone name from command line: {Config.ZONE_NAME}")

    if args.camera:
        Config.CAMERA_NAME = args.camera
        print(f"Using camera name from command line: {Config.CAMERA_NAME}")

    if args.threshold:
        Config.MAX_PERSON_COUNT = args.threshold
        print(
            f"Using crowd threshold from command line: {Config.MAX_PERSON_COUNT}")

    if args.zone_points:
        try:
            Config.ZONE_POINTS = json.loads(args.zone_points)
            print(f"Using zone points from command line: {Config.ZONE_POINTS}")
        except json.JSONDecodeError as e:
            print(f"Error parsing zone points JSON: {e}")
            return

    # Create and run the system
    system = CrowdDetectionSystem()
    system.run()


if __name__ == "__main__":
    main()
