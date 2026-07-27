"""
ROS2 Spatial Coordinates to HTTP REST Gateway
Part of HappyCoding Labs B2B AI Enterprise Modules.

Bridges ROS 2 physical robotics vision nodes (3D spatial coordinates x, y, z, roll, pitch, yaw)
with HTTP REST APIs for Web Application and AI Agent control.
"""

from typing import Dict, Any
import datetime

class ROS2SpatialGateway:
    def __init__(self):
        self.node_name = "ros2_spatial_http_gateway"
        self.contact_email = "happycodinglabs@gmail.com"

    def format_spatial_payload(self, target_id: str, x: float, y: float, z: float, confidence: float) -> Dict[str, Any]:
        """
        Formats 3D spatial target coordinates into Web-friendly REST response payload.
        """
        return {
            "status": "active",
            "target_id": target_id,
            "coordinates": {
                "x": round(x, 4),
                "y": round(y, 4),
                "z": round(z, 4),
                "unit": "meters",
                "frame": "camera_color_optical_frame"
            },
            "confidence": confidence,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "contact": self.contact_email
        }
