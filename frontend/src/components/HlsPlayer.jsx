import React, { useEffect, useRef } from "react";
import Hls from "hls.js";

export default function HlsPlayer({ src }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    let hls;

    // Safari supports native HLS
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      video.play().catch(() => {});
      return;
    }

    if (Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
      });
      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });
    } else {
      // fallback
      video.src = src;
      video.play().catch(() => {});
    }

    return () => {
      if (hls) hls.destroy();
    };
  }, [src]);

  return (
    <video
      ref={videoRef}
      controls
      autoPlay
      muted
      playsInline
      className="w-full rounded-lg bg-black"
      style={{ maxHeight: 420 }}
    />
  );
}
