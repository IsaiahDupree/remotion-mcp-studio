#!/usr/bin/env python3
"""
Webhook Utility for Smart Text-on-Video Overlay Tool

Sends webhook notifications when videos are processed, perfect for integration
with Make.com, Zapier, or other automation platforms.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional

# Set up logging
log = logging.getLogger("smart_overlay.webhook")


class WebhookNotifier:
    """Sends webhook notifications when videos are processed."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize the webhook notifier.
        
        Args:
            webhook_url: URL to send webhook notifications to
        """
        self.webhook_url = webhook_url
    
    def set_webhook_url(self, url: str) -> None:
        """Set the webhook URL.
        
        Args:
            url: URL to send webhook notifications to
        """
        self.webhook_url = url
    
    def notify_video_processed(self, metadata: Dict[str, Any]) -> bool:
        """Send a webhook notification for a processed video.
        
        Args:
            metadata: Video processing metadata
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not self.webhook_url:
            log.warning("No webhook URL configured, skipping notification")
            return False
        
        try:
            # Prepare payload
            payload = {
                "event": "video_processed",
                "timestamp": metadata.get("timestamp", ""),
                "video": {
                    "original_name": metadata.get("original_name", ""),
                    "new_name": metadata.get("new_name", ""),
                    "overlay_text": metadata.get("overlay_text", ""),
                    "prompt": metadata.get("prompt", ""),
                    "position": {
                        "x": metadata.get("position_x", 0),
                        "y": metadata.get("position_y", 0)
                    },
                    "duration": metadata.get("duration", 0),
                    "font_style": metadata.get("font_style", "")
                }
            }
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                log.info(f"Webhook notification sent successfully: {response.status_code}")
                return True
            else:
                log.error(f"Failed to send webhook notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log.error(f"Error sending webhook notification: {e}")
            return False
    
    def notify_batch_complete(self, batch_info: Dict[str, Any]) -> bool:
        """Send a webhook notification for a completed batch.
        
        Args:
            batch_info: Batch processing information
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not self.webhook_url:
            log.warning("No webhook URL configured, skipping notification")
            return False
        
        try:
            # Prepare payload
            payload = {
                "event": "batch_complete",
                "timestamp": batch_info.get("timestamp", ""),
                "batch": {
                    "total_videos": batch_info.get("total_videos", 0),
                    "successful_videos": batch_info.get("successful_videos", 0),
                    "failed_videos": batch_info.get("failed_videos", 0),
                    "output_directory": batch_info.get("output_directory", ""),
                    "mapping_file": batch_info.get("mapping_file", ""),
                    "prompt": batch_info.get("prompt", "")
                }
            }
            
            # Send webhook
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                log.info(f"Batch complete webhook notification sent successfully: {response.status_code}")
                return True
            else:
                log.error(f"Failed to send batch complete webhook notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log.error(f"Error sending batch complete webhook notification: {e}")
            return False
