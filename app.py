import time
import logging
import schedule
import base64
import requests
import os
import json
from datetime import datetime
from pytz import timezone

from config import Config
from airtable_client import AirtableClient
from media_modifier import MediaModifier
from poster import SocialPoster
from creator import ContentCreator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)

def get_target_platforms():
    """
    Determine platforms based on the time logic from n8n.
    """
    ist = timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)
    hour = now_ist.hour
    
    platforms = ["Instagram", "Facebook", "Twitter", "LinkedIn", "Pinterest"]
    if hour >= 23 or hour < 11:
        platforms.append("Thread")
        
    return platforms

PROGRESS_FILE = "posting_progress.json"

def get_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

def update_record_progress(record_id, account_name):
    progress = get_progress()
    if record_id not in progress:
        progress[record_id] = []
    if account_name and account_name not in progress[record_id]:
        progress[record_id].append(account_name)
    save_progress(progress)
    return progress.get(record_id, [])

def process_pending_posts(target_account=None):
    """
    Fetches the oldest pending record and posts it to the target account.
    """
    if not target_account:
        logger.warning("process_pending_posts called without target_account. Skipping.")
        return

    logger.info(f"Checking for pending posts for {target_account}...")
    
    airtable = AirtableClient(
        api_key=Config.AIRTABLE_API_KEY,
        base_id=Config.AIRTABLE_BASE_ID,
        table_name=Config.AIRTABLE_TABLE_NAME
    )
    
    records = airtable.get_pending_posts(max_records=1)
    if not records:
        logger.info("No pending posts found.")
        return

    record = records[0]
    record_id = record['id']
    fields = record['fields']
    
    # Check if this account already posted this record
    posted_accounts = update_record_progress(record_id, None) # Get current progress without adding
    if target_account in posted_accounts:
        logger.info(f"Record {record_id} already processed for {target_account}. Skipping.")
        return

    creator = ContentCreator(
        model_name=Config.LLM_MODEL,
        api_key=Config.OPENAI_API_KEY,
        provider=Config.LLM_PROVIDER,
        google_api_key=Config.GOOGLE_API_KEY,
        openrouter_api_key=Config.OPENROUTER_API_KEY
    )
    media_mod = MediaModifier(
        Config.IMAGE_METADATA_API, 
        Config.VIDEO_METADATA_API,
        Config.CLOUDINARY_API_URL,
        Config.CLOUDINARY_API_KEY,
        Config.CLOUDINARY_UPLOAD_PRESET
    )
    platforms = get_target_platforms()

    webhook_url = Config.MAKE_WEBHOOKS.get(target_account)
    if not webhook_url or webhook_url == "URL_HERE":
        logger.warning(f"No webhook configured for {target_account}. Marking as processed.")
        update_record_progress(record_id, target_account)
        return

    logger.info(f"Processing Record {record_id} for {target_account}...")
    
    title = fields.get("Title", "")
    description = fields.get("Description", "")
    hashtags = fields.get("HashTags", "")
    image_url = fields.get("ImageLInk")
    video_url = fields.get("Videolink")
    video_thumbnail = fields.get("VideoCoverImage", "")

    post_success = True
    try:
        # Process Image
        if image_url and not video_url:
            media_mod.modify_image_metadata(image_url)
            base64_image = ""
            try:
                resp = requests.get(image_url)
                resp.raise_for_status()
                base64_image = base64.b64encode(resp.content).decode('utf-8')
            except Exception as e:
                logger.error(f"Failed to download image: {e}")
                post_success = False
                
            if post_success:
                for platform in platforms:
                    content = creator.create_image_post(platform, title, description, hashtags)
                    if not content: continue
                    poster = SocialPoster(webhook_url, api_key=Config.MAKE_API_KEY)
                    poster.post_image([platform], base64_image, content.get('title', ''), content.get('caption', ''))
                    time.sleep(2)
                    
        # Process Video
        elif video_url:
            mod_video_url = media_mod.modify_video_metadata(video_url)
            for platform in platforms:
                content = creator.create_video_post(platform, title, description, hashtags)
                if not content: continue
                poster = SocialPoster(webhook_url, api_key=Config.MAKE_API_KEY)
                poster.post_video([platform], mod_video_url, content.get('title', ''), content.get('caption', ''), video_thumbnail)
                time.sleep(2)
        else:
            logger.warning(f"No media found for record {record_id}")
            post_success = False

    except Exception as e:
        logger.exception(f"Error during posting to {target_account}: {e}")
        post_success = False

    # Mark as Done immediately as per user request ("immediately to Done")
    # This allows the user to see the record as finished while other profiles 
    # continue to process it in the background using the local progress file.
    update_record_progress(record_id, target_account)
    airtable.mark_as_posted(record_id)
    logger.info(f"Processed {target_account} for record {record_id}. Status set to DONE.")

def main():
    logger.info("Starting Social Media Automation Scheduler...")
    
    active_profiles = [acc for acc, url in Config.MAKE_WEBHOOKS.items() if url and url != "URL_HERE"]
    
    for account_name in active_profiles:
        time_str = Config.POSTING_TIMES.get(account_name)
        if not time_str:
            logger.warning(f"No posting time found for {account_name}. Skipping scheduling.")
            continue
            
        logger.info(f"Scheduling {account_name} for {time_str} daily.")
        # Use a default argument in lambda to capture the current account_name correctly
        schedule.every().day.at(time_str).do(lambda acc=account_name: process_pending_posts(target_account=acc))
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
