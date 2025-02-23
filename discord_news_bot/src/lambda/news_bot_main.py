import boto3
import json
import os
import logging
import traceback
import nacl.signing
import nacl.exceptions
from sources.bluesky_client import fetch_bluesky_posts
from discord_poster import post_to_discord

# AWS Clients
secrets_client = boto3.client("secretsmanager")

# Environment Variables
discord_secret_arn = os.getenv("DISCORD_BOT_SECRET_ARN")

# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Change to DEBUG if needed


def log_and_trace(level, message, error=None):
    """
    Logs messages with structured formatting.
    """
    if error:
        message = (
            f"{message} | Exception: {str(error)} | Traceback: {traceback.format_exc()}"
        )
        logger.error(message)
    else:
        logger.log(level, message)


def get_discord_secrets():
    """
    Fetches Discord bot secrets from AWS Secrets Manager.
    """
    try:
        log_and_trace(logging.DEBUG, "Fetching Discord secrets")
        response = secrets_client.get_secret_value(SecretId=discord_secret_arn)
        log_and_trace(logging.DEBUG, f"Retrieved discord secrets: {response}")
        secret = json.loads(response["SecretString"])
        return secret.get("token"), secret.get("appId"), secret.get("publicKey")
    except secrets_client.exceptions.ResourceNotFoundException:
        log_and_trace(
            logging.ERROR,
            "Secrets not found",
            secrets_client.exceptions.ResourceNotFoundException,
        )
    except Exception as e:
        log_and_trace(logging.ERROR, "Error fetching Discord secrets", e)
        raise


def verify_signature(event, public_key):
    """
    Verifies Discord request signature using the public key.
    """
    try:
        signature = event["headers"].get("x-signature-ed25519", "")
        timestamp = event["headers"].get("x-signature-timestamp", "")
        body = event.get("body", "")

        verify_key = nacl.signing.VerifyKey(
            public_key, encoder=nacl.encoding.HexEncoder
        )
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        log_and_trace(logging.DEBUG, "Signature verification successful")
        return True
    except nacl.exceptions.BadSignatureError:
        log_and_trace(logging.WARNING, "Signature verification failed")
        return False
    except Exception as e:
        log_and_trace(logging.ERROR, "Unexpected error in signature verification", e)
        return False


def process_scheduled_event():
    """
    Fetches Bluesky posts and posts them to Discord.
    """
    try:
        log_and_trace(logging.INFO, "Fetching Bluesky posts...")
        posts = fetch_bluesky_posts()

        for post in posts:
            log_and_trace(
                logging.DEBUG, f"Posting to Discord: {post.get('author_name')}"
            )
            post_to_discord(post, source="bluesky")

        log_and_trace(logging.INFO, "Successfully posted updates to Discord.")
        return {
            "statusCode": 200,
            "body": json.dumps("News Bot successfully posted updates to Discord."),
        }
    except Exception as e:
        log_and_trace(logging.ERROR, "Error while fetching or posting Bluesky news", e)
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}


def lambda_handler(event, context):
    """
    Main Lambda handler.
    Determines if the event is a scheduled event (news_post) or a Discord interaction.
    """
    try:
        log_and_trace(logging.DEBUG, f"Received event: {json.dumps(event)}")

        # Check if the event is an EventBridge (scheduled) event
        is_scheduled_event = event.get("source") == "aws.events"
        task_type = event.get("detail", {}).get("task", "")

        if is_scheduled_event and task_type == "news_post":
            return process_scheduled_event()

        # Handle Discord interactions
        if "headers" in event:
            TOKEN, APP_ID, PUBLIC_KEY = get_discord_secrets()

            if not verify_signature(event, PUBLIC_KEY):
                return {"statusCode": 401, "body": "Invalid request signature"}

            body = json.loads(event["body"])
            interaction_type = body.get("type")

            if interaction_type == 1:  # Discord PING event
                return {"statusCode": 200, "body": json.dumps({"type": 1})}

        log_and_trace(logging.WARNING, "Event did not match any known type.")
        return {"statusCode": 400, "body": "Unknown event type"}

    except Exception as e:
        log_and_trace(logging.ERROR, "Unexpected error in Lambda handler", e)
        return {
            "statusCode": 500,
            "body": json.dumps(f"Internal Server Error: {str(e)}"),
        }
