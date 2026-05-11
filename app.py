import time
import logging
import schedule
import base64
import requests
import os
import json
import threading
from datetime import datetime
from pytz import timezone
from flask import Flask

from config import Config
from airtable_client import AirtableClient
from media_modifier import MediaModifier
from poster import SocialPoster
from creator import ContentCreator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Health Check Server (required for Render free Web Service) ---
health_app = Flask(__name__)

@health_app.route("/")
def health():
    return "Social Media Scheduler is running!", 200

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting health-check server on port {port}...")
    health_app.run(host="0.0.0.0", port=port)
# ------------------------------------------------------------------

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
    """Mark account_name as done for this record_id. Returns the updated list."""
    progress = get_progress()
    if record_id not in progress:
        progress[record_id] = []
    if account_name and account_name not in progress[record_id]:
        progress[record_id].append(account_name)
    save_progress(progress)
    return progress.get(record_id, [])

def get_all_active_profiles():
    """Return all profile names that have a valid webhook URL."""
    return [acc for acc, url in Config.MAKE_WEBHOOKS.items() if url and url != "URL_HERE"]

def all_profiles_done(record_id):
    """
    Returns True only when every active profile has been recorded in progress
    for this record (either posted successfully or skipped due to no webhook).
    """
    active_profiles = set(get_all_active_profiles())
    # Also include profiles that were intentionally skipped (no webhook)
    skipped_profiles = set(
        acc for acc, url in Config.MAKE_WEBHOOKS.items()
        if not url or url == "URL_HERE"
    )
    # All profiles that should be counted as "done"
    expected_profiles = active_profiles | skipped_profiles
    done_profiles = set(get_progress().get(record_id, []))
    remaining = expected_profiles - done_profiles
    if remaining:
        logger.info(f"Record {record_id} still waiting on profiles: {remaining}")
        return False
    return True

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
        logger.warning(f"No webhook configured for {target_account}. Skipping and marking as processed.")
        update_record_progress(record_id, target_account)
        # Check if ALL profiles are now done after this skip
        if all_profiles_done(record_id):
            airtable.mark_as_posted(record_id)
            logger.info(f"All profiles done for record {record_id}. Status set to DONE.")
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

    # Only save progress if the post was successful
    if post_success:
        update_record_progress(record_id, target_account)
        logger.info(f"Recorded successful post for {target_account} on record {record_id}.")
        # Check if ALL profiles have now completed — only then mark Airtable as Done
        if all_profiles_done(record_id):
            airtable.mark_as_posted(record_id)
            logger.info(f"✅ All profiles done for record {record_id}. Status set to DONE in Airtable.")
        else:
            logger.info(f"⏳ Record {record_id}: {target_account} done. Waiting for remaining profiles before marking Done.")
    else:
        logger.warning(f"❌ Post failed for {target_account} on record {record_id}. NOT marking as done. Will retry next schedule.")

def ist_to_utc(time_str):
    """
    Convert a time string in IST (HH:MM) to UTC (HH:MM).
    Render servers run in UTC, but users enter times in IST (UTC+5:30).
    """
    from datetime import date, time as dt_time
    import pytz
    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc
    hour, minute = map(int, time_str.split(":"))
    # Combine with today's date and localize to IST
    ist_dt = ist.localize(datetime.combine(date.today(), dt_time(hour, minute)))
    # Convert to UTC
    utc_dt = ist_dt.astimezone(utc)
    return utc_dt.strftime("%H:%M")

def main():
    logger.info("Starting Social Media Automation Scheduler...")
    logger.info("NOTE: Posting times are entered in IST and auto-converted to UTC for scheduling.")
    
    active_profiles = [acc for acc, url in Config.MAKE_WEBHOOKS.items() if url and url != "URL_HERE"]
    
    for account_name in active_profiles:
        time_str_ist = Config.POSTING_TIMES.get(account_name)
        if not time_str_ist:
            logger.warning(f"No posting time found for {account_name}. Skipping scheduling.")
            continue

        time_str_utc = ist_to_utc(time_str_ist)
        logger.info(f"Scheduling {account_name} at {time_str_ist} IST ({time_str_utc} UTC) daily.")
        # Use a default argument in lambda to capture the current account_name correctly
        schedule.every().day.at(time_str_utc).do(lambda acc=account_name: process_pending_posts(target_account=acc))
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Start Flask health-check server in a background daemon thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    # Run the scheduler (blocks forever)
    main()
