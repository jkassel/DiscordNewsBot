from atproto import Client
import boto3
import json
import os
import logging
import time

# Configure Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger()

# AWS Configuration
bluesky_secret_arn = os.getenv("BLUESKY_SECRET_ARN")
REGION_NAME = "us-east-1"
S3_BUCKET = os.getenv("S3_BUCKET", "news-bot-processed-posts")
S3_KEY = "processed_posts.json"
MAX_RETRIES = 3
FETCH_LIMIT = 10  # Adjust if needed

# AWS Clients
secrets_client = boto3.client("secretsmanager", region_name=REGION_NAME)
s3_client = boto3.client("s3", region_name=REGION_NAME)


# Retrieve Bluesky Credentials from Secrets Manager
def get_bluesky_credentials():
    try:
        response = secrets_client.get_secret_value(SecretId=bluesky_secret_arn)
        secret = json.loads(response["SecretString"])
        return secret.get("username"), secret.get("password")
    except Exception as e:
        logger.error(f"Error retrieving Bluesky credentials: {e}")
        return None, None


# Load Processed Posts from S3
def load_processed_posts():
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        data = json.loads(response["Body"].read().decode("utf-8"))
        return set(data.get("processed_posts", []))
    except s3_client.exceptions.NoSuchKey:
        logger.warning("Processed posts file not found. Starting fresh.")
        return set()
    except Exception as e:
        logger.error(f"Error loading processed posts from S3: {e}")
        return set()


# Save Processed Posts to S3
def save_processed_posts(processed_posts):
    try:
        data = json.dumps({"processed_posts": list(processed_posts)})
        s3_client.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=data)
        logger.debug("Successfully saved processed posts to S3.")
    except Exception as e:
        logger.error(f"Error saving processed posts to S3: {e}")


# Extracts the post URL, prioritizing external embeds
def extract_post_url(post):
    if hasattr(post, "embed") and post.embed:
        if hasattr(post.embed, "external") and post.embed.external:
            return post.embed.external.uri  # ✅ Use external URI if available
    return (
        f"https://bsky.app/profile/{post.author.handle}/post/"
        f"{post.uri.split('/')[-1]}"
    )  # ✅ Fallback to Bluesky post URL


# Fetch Feeds and Posts from Bluesky
def fetch_bluesky_posts():
    username, password = get_bluesky_credentials()
    if not username or not password:
        logger.warning("Bluesky credentials not found. Aborting request.")
        return []

    processed_posts = load_processed_posts()
    new_posts = []

    client = Client()
    try:
        logger.debug("Authenticating with Bluesky API...")
        client.login(username, password)
        logger.info("✅ Successfully authenticated with Bluesky.")

        logger.debug("Fetching user preferences...")
        prefs = client.app.bsky.actor.get_preferences()

        logger.debug("Identifying saved feeds...")
        saved_feeds = []
        for pref in prefs.preferences:
            if pref.py_type == "app.bsky.actor.defs#savedFeedsPrefV2":
                for item in pref.items:
                    if item.type == "feed":
                        saved_feeds.append(item.value)

        if not saved_feeds:
            logger.warning("⚠️ No saved feeds found.")
            return []

        logger.info(f"📢 Found {len(saved_feeds)} saved feeds.")

        total_new_post_cnt = 0

        for feed_uri in saved_feeds:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    logger.info(
                        f"🔍 Attempt {attempt}: Fetching posts from feed {feed_uri}..."
                    )

                    # ✅ Get Feed Details
                    feed_data = client.app.bsky.feed.get_feed_generator(
                        {"feed": feed_uri}
                    )
                    feed_name = feed_data.view.display_name
                    feed_creator = feed_data.view.creator.handle
                    logger.info(f"📢 Processing feed: {feed_name} by {feed_creator}")

                    # ✅ Get Posts from Feed
                    response = client.app.bsky.feed.get_feed(
                        {"feed": feed_uri, "limit": FETCH_LIMIT}
                    )
                    feed_posts = response.feed  # ✅ [:2] Limit to the first 2 posts

                    if not feed_posts:
                        logger.warning(f"⚠️ No posts found in feed {feed_uri}.")
                        break

                    logger.info(
                        f"📢 Found {len(feed_posts)} posts in feed {feed_name}."
                    )
                    for item in feed_posts:
                        logger.debug(f"feed_post item: {item}")
                        post_id = item.post.uri
                        if not post_id:
                            logger.warning(
                                f"⚠️ Skipping post with missing post_id: {item}"
                            )
                            continue

                        if post_id in processed_posts:
                            logger.debug(
                                f"🔄 Skipping already processed post: {post_id}"
                            )
                            continue

                        author = item.post.author
                        record = item.post.record

                        post = {
                            "title": (
                                record.text[:100] + "..."
                                if hasattr(record, "text")
                                else "Untitled Post"
                            ),
                            "author_name": author.display_name,
                            "author_handle": author.handle,
                            "author_avatar": author.avatar,
                            "content": (
                                record.text if hasattr(record, "text") else "No Content"
                            ),
                            "post_url": extract_post_url(item.post),
                            "bluesky_link": f"https://bsky.app/profile/{author.handle}"
                            f"/post/{post_id.split('/')[-1]}",
                            "image_url": extract_image_url(item.post),
                            "likes": item.post.like_count or 0,
                            "reposts": item.post.repost_count or 0,
                            "replies": item.post.reply_count or 0,
                            "quotes": item.post.quote_count or 0,
                            "feed_name": feed_name,
                        }

                        logger.info(f"✅ Processed Post: {post}")
                        new_posts.append(post)
                        total_new_post_cnt += 1
                        processed_posts.add(post_id)

                    logger.info(f"📢 Feed: {feed_name} processed")

                    break  # Break out of retry loop on success

                except Exception as e:
                    logger.error(f"⚠️ Error fetching feed {feed_uri}: {e}")
                    time.sleep(2)  # Retry delay

        save_processed_posts(processed_posts)

        logger.info(
            f"✅ Total new posts retrieved across all feeds: {total_new_post_cnt}"
        )

        return new_posts

    except Exception as e:
        logger.error(f"❌ Critical error fetching posts from Bluesky: {e}")
        return []


# Helper Function to Extract Image URL
def extract_image_url(post):
    """
    Extracts the image URL from a post embed.
    """
    if hasattr(post, "embed") and post.embed:
        if hasattr(post.embed, "external") and post.embed.external:
            return post.embed.external.thumb  # External news article image
        if hasattr(post.embed, "images") and post.embed.images:
            return post.embed.images[0].fullsize  # First image in the list

    return ""
