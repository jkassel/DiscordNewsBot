import feedparser
import logging
import os


def fetch_rss_posts():
    """
    Fetches and parses articles from configured RSS feeds.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    RSS_FEEDS = os.getenv("RSS_FEEDS", "").split(",")
    if not RSS_FEEDS or RSS_FEEDS == [""]:
        logger.warning("No RSS feeds configured. Skipping RSS fetch.")
        return []

    articles = []
    for feed_url in RSS_FEEDS:
        logger.info(f"Fetching RSS feed: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Limit to 5 latest articles per feed
                article = {
                    "title": entry.title,
                    "content": entry.summary,
                    "author_name": entry.get("author", "Unknown Author"),
                    "post_url": entry.link,
                    "image_url": entry.get("media_content", [{}])[0].get("url", ""),
                    "source": "rss",
                }
                articles.append(article)
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")

    return articles
