import logging
import requests

logger = logging.getLogger(__name__)

class MediaModifier:
    def __init__(self, image_api_url: str, video_api_url: str, cloudinary_url: str, cloudinary_api_key: str, cloudinary_preset: str):
        self.image_api_url = image_api_url
        self.video_api_url = video_api_url
        self.cloudinary_url = cloudinary_url
        self.cloudinary_api_key = cloudinary_api_key
        self.cloudinary_preset = cloudinary_preset

    def modify_image_metadata(self, image_url: str):
        try:
            logger.info(f"Triggering image metadata modification for: {image_url}")
            payload = {"image_url": image_url}
            response = requests.post(self.image_api_url, json=payload)
            response.raise_for_status()
            logger.info("Successfully triggered image metadata modification.")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to modify image metadata: {e}")
            return None

    def modify_video_metadata(self, video_url: str):
        try:
            logger.info(f"Triggering video metadata modification for: {video_url}")
            payload = {"video_url": video_url}
            response = requests.post(self.video_api_url, json=payload)
            response.raise_for_status()
            logger.info("Successfully triggered video metadata modification.")
            # Expecting the modified URL in the response
            return response.json().get('video_url', video_url)
        except Exception as e:
            logger.error(f"Failed to modify video metadata: {e}")
            return video_url
