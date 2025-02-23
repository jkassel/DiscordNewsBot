import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the `src/lambda` directory to sys.path so imports work
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/lambda"))
)

from sources_registry import fetch_news_from_sources  # noqa: E402
from discord_poster import post_to_discord, get_discord_secrets  # noqa: E402


class TestDiscordNewsBot(unittest.TestCase):

    @patch.dict(os.environ, {"RSS_FEEDS": "https://example.com/feed"})
    @patch("sources.bluesky_client.fetch_bluesky_posts", return_value=[{"title": "Bluesky Post", "source": "bluesky"}])
    @patch("sources.rss_client.fetch_rss_posts", return_value=[{"title": "RSS Article", "source": "rss"}])
    @patch("sources.bluesky_client.get_bluesky_credentials", return_value=["test_user", "test_pass"])
    def test_fetch_news_from_sources(self, mock_rss, mock_bluesky, mock_credentials):
        """Test fetching news from Bluesky and RSS sources."""
        posts = fetch_news_from_sources()  # Call the function, not the mock
        print(posts)
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["source"], "bluesky")
        self.assertEqual(posts[1]["source"], "rss")

    @patch("discord_poster.get_discord_secrets", return_value=("https://fake-webhook.com", "fake_forum_id", "fake_server_id", "fake_token"))
    @patch("discord_poster.post_to_discord")
    def test_post_to_discord(self, mock_post, mock_secrets):
        """Test posting to Discord with mocked secrets."""
        post = {"title": "Test Post", "source": "rss"}
        post_to_discord(post, source=post["source"])
        mock_post.assert_called_once()

    @patch("sources.bluesky_client.fetch_bluesky_posts", return_value=[{"title": "Bluesky API Post", "source": "bluesky"}])
    @patch("sources.rss_client.fetch_rss_posts", return_value=[{"title": "RSS API Article", "source": "rss"}])
    def test_fetch_news_from_sources_with_api_calls(self, mock_rss, mock_bluesky):
        """Test fetching news with API-style mocked responses."""
        posts = fetch_news_from_sources()
        self.assertTrue(len(posts) >= 2)  # Ensures at least RSS & Bluesky are included


if __name__ == "__main__":
    unittest.main()
