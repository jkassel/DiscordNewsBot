import os
from dotenv import load_dotenv
from aws_cdk import App, Environment
from discord_news_bot_stack import DiscordNewsBotStack

# Load environment variables from .env file
load_dotenv()

app = App()

env = Environment(
    account=os.getenv("AWS_ACCOUNT"),
    region=os.getenv("AWS_REGION"),
)

app_name = os.getenv("APP_NAME")

DiscordNewsBotStack(app, f"{app_name}DiscordNewsBotStack", env=env, app_name=app_name)

app.synth()
