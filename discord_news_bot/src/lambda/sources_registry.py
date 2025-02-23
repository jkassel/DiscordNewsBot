from sources.bluesky_client import fetch_bluesky_posts
from sources.rss_client import fetch_rss_posts
import os


def get_active_sources():
    """
    Returns a list of active data sources.
    """
    sources = os.getenv("ACTIVE_SOURCES", "bluesky,rss").split(",")
    return [s.strip() for s in sources if s.strip()]


def fetch_news_from_sources():
    """
    Fetches news from all active sources.
    """
    posts = []

    if "bluesky" in get_active_sources():
        posts.extend(fetch_bluesky_posts())
    if "rss" in get_active_sources():
        posts.extend(fetch_rss_posts())

    return posts
