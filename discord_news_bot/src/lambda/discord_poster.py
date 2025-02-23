import boto3
import json
import os
import logging
import requests
import time

# Configure Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger()

# AWS Secrets Manager Configuration
discord_secret_arn = os.getenv("DISCORD_BOT_SECRET_ARN")
REGION_NAME = "us-east-1"
DISCORD_POST_TYPE = os.getenv("DISCORD_POST_TYPE", "forum")  # Default to 'forum'
API_URL = "https://discord.com/api/v10"
MAX_ACTIVE_THREADS = os.getenv("MAX_ACTIVE_THREADS", 200)


# Retrieve Discord Webhook URL from Secrets Manager
def get_discord_secrets():
    client = boto3.client("secretsmanager", region_name=REGION_NAME)
    try:
        response = client.get_secret_value(SecretId=discord_secret_arn)
        secret = json.loads(response["SecretString"])
        return (
            secret.get("webhookUrl"),
            secret.get("forumChannelId"),
            secret.get("forumServerId"),
            secret.get("token"),
        )
    except Exception as e:
        logger.error(f"Error retrieving Discord Webhook URL: {str(e)}")
        return None


# Format a professional Discord embed for Bluesky news posts
def format_bluesky_embed(post):
    """
    Generates a well-formatted embed for a Bluesky post.
    """
    embed = {
        "title": post.get("title", "News Update"),
        "description": post.get("content", ""),
        "url": post.get("post_url", ""),
        "color": 3447003,  # Discord blue color
        "footer": {
            "text": (
                f"👍 {post.get('likes', 0)} | "
                f"🔄 {post.get('reposts', 0)} | "
                f"💬 {post.get('replies', 0)} | "
                f"📝 {post.get('quotes', 0)}"
            )
        },
        "author": {
            "name": f"{post.get('author_name', '')} (@{post.get('author_handle', '')})",
            "url": post.get("bluesky_link"),
            "icon_url": post.get("author_avatar", ""),
        },
    }

    # Add embedded article preview (if available)
    if post.get("article_title"):
        article_embed = {
            "title": post["article_title"],
            "description": post.get("article_description", ""),
            "url": post.get("article_url", ""),
        }
        if post.get("image_url"):
            article_embed["image"] = {"url": post["image_url"]}  # Use news thumbnail
        return [embed, article_embed]  # Return two embeds (post + article)

    # Otherwise, add the main post image if available
    if post.get("image_url"):
        embed["image"] = {"url": post["image_url"]}

    return [embed]  # Return as a list


# Fetch Active Threads
def get_active_threads(forum_server_id, forum_channel_id, discord_token):
    """Fetches all active threads in the Discord forum."""
    url = f"{API_URL}/guilds/{forum_server_id}/threads/active"

    headers = {
        "Authorization": f"Bot {discord_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for HTTP failures

        data = response.json()
        threads = data.get("threads", [])

        if threads:
            logger.info(f"✅ Found {len(threads)} active threads.")
            threads = [
                thread
                for thread in data.get("threads", [])
                if str(thread.get("parent_id"))
                == forum_channel_id  # Only archive threads from this forum
            ]
        else:
            logger.info("ℹ️ No active threads found.")

        return threads

    except requests.RequestException as e:
        logger.error(f"❌ Error fetching active threads: {str(e)}")
        return []


def archive_thread(discord_token, thread_id):
    """Archives a thread by sending a PATCH request to Discord API."""
    url = f"https://discord.com/api/v10/channels/{thread_id}"
    payload = {"archived": True}

    headers = {
        "Authorization": f"Bot {discord_token}",
        "Content-Type": "application/json",
    }

    response = requests.patch(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"✅ Archived thread {thread_id}")
    else:
        print(
            f"❌ Failed to archive thread {thread_id}: "
            f"{response.status_code} {response.text}"
        )


# Archive Oldest Thread (if more than 200 are active)
def archive_excess_threads(forum_channel_id, forum_server_id, discord_token):
    """Archives the oldest thread if there are more than 200 active."""

    threads = get_active_threads(
        forum_channel_id=forum_channel_id,
        forum_server_id=forum_server_id,
        discord_token=discord_token,
    )

    if len(threads) <= MAX_ACTIVE_THREADS:
        print(
            f"✅ Only {len(threads)} active threads "
            f"in forum {forum_channel_id}. No need to archive."
        )
        return

    excess_count = len(threads) - MAX_ACTIVE_THREADS
    print(
        f"⚠️ Found {len(threads)} active threads "
        f"in forum {forum_channel_id}. Archiving {excess_count} threads..."
    )

    # Archive the oldest threads first (sorted by ID, which increases over time)
    threads_sorted = sorted(threads, key=lambda t: int(t["id"]))

    for thread in threads_sorted[:excess_count]:
        archive_thread(discord_token=discord_token, thread_id=thread["id"])
        time.sleep(1)  # Rate-limit to avoid hitting Discord API limits


# Post to Discord using Webhook
def post_to_discord(post, source="bluesky"):
    webhook_url, forum_channel_id, forum_server_id, discord_token = (
        get_discord_secrets()
    )
    if not webhook_url:
        logger.warning("Webhook URL not found. Aborting Discord post.")
        return

    # Only apply this formatting to Bluesky posts for now
    if source == "bluesky":
        embeds = format_bluesky_embed(post)
    else:
        embeds = [
            {
                "title": post.get("title", "News Update"),
                "description": post.get("content", ""),
                "url": post.get("url", ""),
                "color": 3447003,
            }
        ]

    # Webhook Payload with Custom Name & Avatar
    payload = {
        "username": post.get("author_name", "News Bot"),  # Custom bot name
        "avatar_url": post.get("author_avatar", ""),  # Custom avatar
        "embeds": embeds,
    }

    # Handle Forum Posting
    if DISCORD_POST_TYPE == "forum":
        payload["thread_name"] = post.get(
            "title", post.get("author_name", "News Thread")
        )
        # payload["content"] = post.get("title", "")
        archive_excess_threads(
            forum_channel_id=forum_channel_id,
            forum_server_id=forum_server_id,
            discord_token=discord_token,
        )

    try:
        logger.debug(f"Sending payload to Discord: {payload}")
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        logger.info(
            f"✅ Successfully posted to Discord as "
            f"{post.get('author_name')} (Type: {DISCORD_POST_TYPE})"
        )
    except requests.RequestException as e:
        logger.error(f"❌ Error posting to Discord: {str(e)}")
