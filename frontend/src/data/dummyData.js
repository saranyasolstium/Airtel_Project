export const alertsData = [
  {
    "id": 1,
    "type": "critical",
    "category": "Unauthorized Entry",
    "message": "Person detected in restricted zone - Substation Room B",
    "timestamp": "2025-12-29 14:23:15",
    "camera": "CAM-012",
    "location": "North Perimeter",
    "status": "active"
  },
  {
    "id": 2,
    "type": "warning",
    "category": "PPE Compliance",
    "message": "Personnel without helmet detected in Data Floor 3",
    "timestamp": "2025-12-29 14:18:42",
    "camera": "CAM-045",
    "location": "Data Centre Floor 3",
    "status": "active"
  },
  {
    "id": 3,
    "type": "info",
    "category": "Vehicle LPR",
    "message": "Vehicle ABC-1234 verified - Access granted",
    "timestamp": "2025-12-29 14:15:30",
    "camera": "CAM-003",
    "location": "Main Gate",
    "status": "resolved"
  },
  {
    "id": 4,
    "type": "warning",
    "category": "Loitering",
    "message": "Individual detected loitering near Gate 2 for 8 minutes",
    "timestamp": "2025-12-29 14:12:55",
    "camera": "CAM-008",
    "location": "East Gate",
    "status": "active"
  },
  {
    "id": 5,
    "type": "critical",
    "category": "Crowd Formation",
    "message": "Crowd density exceeds limit (15 people) in Loading Bay",
    "timestamp": "2025-12-29 14:08:12",
    "camera": "CAM-021",
    "location": "Loading Bay",
    "status": "investigating"
  }
];

export const camerasData = [
  {
    "id": "CAM-001",
    "name": "Main Entrance",
    "status": "online",
    "location": "North Gate",
    "health": 98
  },
  {
    "id": "CAM-002",
    "name": "Parking Lot A",
    "status": "online",
    "location": "Parking",
    "health": 95
  },
  {
    "id": "CAM-003",
    "name": "Main Gate LPR",
    "status": "online",
    "location": "Main Gate",
    "health": 100
  },
  {
    "id": "CAM-008",
    "name": "East Perimeter",
    "status": "online",
    "location": "East Gate",
    "health": 92
  },
  {
    "id": "CAM-012",
    "name": "Substation B",
    "status": "online",
    "location": "North Perimeter",
    "health": 97
  },
  {
    "id": "CAM-021",
    "name": "Loading Bay",
    "status": "warning",
    "location": "Loading Bay",
    "health": 78
  },
  {
    "id": "CAM-045",
    "name": "Data Floor 3",
    "status": "online",
    "location": "Data Centre",
    "health": 100
  },
  {
    "id": "CAM-067",
    "name": "Cold Aisle 5",
    "status": "online",
    "location": "Data Centre",
    "health": 94
  }
];

export const vehicleLogsData = [
  {
    "id": 1,
    "licensePlate": "ABC-1234",
    "type": "Sedan",
    "status": "authorized",
    "entryTime": "14:15:30",
    "exitTime": null,
    "dwellTime": "8 min",
    "location": "Parking Bay 12"
  },
  {
    "id": 2,
    "licensePlate": "XYZ-5678",
    "type": "Truck",
    "status": "authorized",
    "entryTime": "13:45:22",
    "exitTime": null,
    "dwellTime": "38 min",
    "location": "Loading Dock"
  },
  {
    "id": 3,
    "licensePlate": "DEF-9012",
    "type": "Van",
    "status": "blacklisted",
    "entryTime": "13:30:15",
    "exitTime": "13:31:20",
    "dwellTime": "1 min",
    "location": "Gate Rejected"
  },
  {
    "id": 4,
    "licensePlate": "GHI-3456",
    "type": "Sedan",
    "status": "authorized",
    "entryTime": "12:20:10",
    "exitTime": "14:10:05",
    "dwellTime": "1h 50m",
    "location": "Visitor Parking"
  }
];

export const ppeComplianceData = [
  {
    "id": 1,
    "zone": "Data Floor 1",
    "personnel": 12,
    "compliant": 12,
    "violations": 0,
    "status": "compliant"
  },
  {
    "id": 2,
    "zone": "Data Floor 2",
    "personnel": 8,
    "compliant": 8,
    "violations": 0,
    "status": "compliant"
  },
  {
    "id": 3,
    "zone": "Data Floor 3",
    "personnel": 15,
    "compliant": 14,
    "violations": 1,
    "status": "violation"
  },
  {
    "id": 4,
    "zone": "Substation Area",
    "personnel": 5,
    "compliant": 5,
    "violations": 0,
    "status": "compliant"
  }
];

export const statisticsData = {
  "totalCameras": 64,
  "activeCameras": 62,
  "activeAlerts": 8,
  "todayIncidents": 23,
  "authorizedVehicles": 45,
  "blacklistedAttempts": 2,
  "ppeCompliance": 97.5,
  "avgResponseTime": "2.3 min"
};

export const trafficMetrics = {
  "gateAThroughput": 145,
  "gateBThroughput": 98,
  "avgWaitTime": "1.2 min",
  "peakHourVehicles": 67,
  "congestionLevel": "low"
};

export const restrictedZoneEvents = [
  {
    "id": 1,
    "zone": "Substation Room B",
    "eventType": "Unauthorized Entry",
    "severity": "critical",
    "timestamp": "14:23:15",
    "personCount": 1
  },
  {
    "id": 2,
    "zone": "Roof Access",
    "eventType": "Door Breach",
    "severity": "warning",
    "timestamp": "13:45:30",
    "personCount": 0
  },
  {
    "id": 3,
    "zone": "Server Room A",
    "eventType": "Authorized Access",
    "severity": "info",
    "timestamp": "12:15:22",
    "personCount": 2
  }
];

export const thermalBreachEvents = [
  {
    "id": 1,
    "aisle": "Cold Aisle 3",
    "temperature": 28.5,
    "threshold": 24,
    "status": "breach",
    "timestamp": "14:10:45"
  },
  {
    "id": 2,
    "aisle": "Cold Aisle 7",
    "temperature": 22.1,
    "threshold": 24,
    "status": "normal",
    "timestamp": "14:09:12"
  }
];
