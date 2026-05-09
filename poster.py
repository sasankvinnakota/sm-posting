import logging
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)

class SocialPoster:
    def __init__(self, make_webhook_url: str, api_key: Optional[str] = None):
        self.make_webhook_url = make_webhook_url
        self.api_key = api_key

    def _get_headers(self):
        headers = {}
        if self.api_key:
            headers["x-make-api-key"] = self.api_key
        return headers

    def post_image(self, platforms: List[str], base64_image: str, title: str, caption: str) -> bool:
        try:
            logger.info(f"Posting image to platforms: {platforms}")
            payload = {
                "platforms": platforms,
                "image": base64_image,
                "title": title,
                "caption": caption,
                "type": "image"
            }
            response = requests.post(
                self.make_webhook_url, 
                json=payload, 
                headers=self._get_headers()
            )
            response.raise_for_status()
            logger.info(f"Successfully dispatched image post to Make webhook for {platforms}")
            return True
        except Exception as e:
            logger.error(f"Failed to post image to {platforms}: {e}")
            return False

    def post_video(self, platforms: List[str], video_url: str, title: str, caption: str, thumbnail_url: str = "") -> bool:
        try:
            logger.info(f"Posting video to platforms: {platforms}")
            payload = {
                "platforms": platforms,
                "video_url": video_url,
                "title": title,
                "caption": caption,
                "thumbnail_url": thumbnail_url,
                "type": "video"
            }
            response = requests.post(
                self.make_webhook_url, 
                json=payload, 
                headers=self._get_headers()
            )
            response.raise_for_status()
            logger.info(f"Successfully dispatched video post to Make webhook for {platforms}")
            return True
        except Exception as e:
            logger.error(f"Failed to post video to {platforms}: {e}")
            return False
