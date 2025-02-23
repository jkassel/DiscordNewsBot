# 📰 Discord News Bot

&#x20; &#x20;

## 🌟 Overview

**Discord News Bot** is a serverless bot that fetches **news from Bluesky and RSS feeds** and posts formatted updates to a **Discord forum or channel**. It is designed for **scalability, modularity, and ease of deployment**.

👉 **Key Features:**

- 📰 Fetches **Bluesky posts** and **RSS articles**.
- 🎨 Posts news in a **formatted Discord embed**.
- ⚡ **Serverless deployment** using **AWS Lambda** and **API Gateway**.
- 🔒 Uses **AWS Secrets Manager** for secure credential storage.
- 🛠 **Extensible design** for adding new news sources.

---

## 📂 Project Structure

```
📦 DiscordNewsBot
├── 💁 src
│   ├── 💁 cdk                # AWS CDK Infrastructure
│   │   ├── app.py           # CDK entry point
│   │   ├── cdk.json         # CDK configuration
│   │   └── discord_news_bot_stack.py # Stack definition
│   ├── 💁 lambda             # Lambda function code
│   │   ├── news_bot_main.py  # Lambda entry point
│   │   ├── discord_poster.py # Handles Discord posting
│   │   ├── sources
│   │   │   ├── bluesky_client.py  # Fetches Bluesky posts
│   │   │   ├── rss_client.py      # Fetches RSS news
│   │   │   └── sources_registry.py # Manages active sources
├── 💁 tests                   # Unit tests
├── 💁 .github/workflows       # CI/CD automation
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation (YOU ARE HERE)
└── Makefile                   # Simplified setup and deployment
```

---

## 🚀 Deployment Guide

### **1⃣ Prerequisites**

- ✅ Python 3.11+ installed ([Download](https://www.python.org/downloads/))
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ AWS CDK installed:
  ```sh
  npm install -g aws-cdk
  ```
- ✅ [Discord Bot Token](https://discord.com/developers/applications) and API credentials.

---

### **2⃣ Installation**

Clone the repository and install dependencies:

```sh
git clone https://github.com/YOUR_GITHUB_USERNAME/DiscordNewsBot.git
cd DiscordNewsBot
pip install -r requirements.txt
```

---

### **3⃣ AWS Setup**

Run **CDK Bootstrap** (one-time setup for your AWS account):

```sh
cdk bootstrap
```

---

### **4⃣ Deploy to AWS**

```sh
cdk deploy
```

Upon successful deployment, you will see the **API Gateway endpoint** for the bot.

---

### **5⃣ Configure Secrets in AWS Secrets Manager**

Use the **AWS CLI** to store credentials securely:

```sh
aws secretsmanager create-secret \
    --name OurCircle/PROD/NewsBot/DiscordSecrets \
    --secret-string '{"token": "YOUR_DISCORD_BOT_TOKEN", "webhookUrl": "YOUR_DISCORD_WEBHOOK_URL"}'
```

---

### **6⃣ Testing Locally**

To run locally, create a `.env` file:

```sh
echo "DISCORD_BOT_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:OurCircle/PROD/NewsBot/DiscordSecrets" > .env
```

Run:

```sh
python src/lambda/news_bot_main.py
```

---

## 🛠 Troubleshooting

| Issue                           | Solution                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| ``** when retrieving Secrets**  | Ensure the secret name **exactly matches** (case-sensitive). Run `aws secretsmanager list-secrets` to verify. |
| **Lambda permissions error**    | Check the IAM role attached to the Lambda in the AWS Console. It must allow `secretsmanager:GetSecretValue`.  |
| **CDK deployment fails**        | Run `cdk synth` to validate before deployment. Ensure AWS credentials are set up (`aws configure`).           |
| **Bluesky posts not appearing** | Verify Bluesky credentials in **Secrets Manager**. Ensure the bot has access to saved feeds.                  |

---

## 🌟 Architecture Overview



- **AWS API Gateway**: Handles incoming requests from Discord.
- **AWS Lambda**: Processes news updates and posts to Discord.
- **AWS Secrets Manager**: Stores Discord & Bluesky credentials securely.
- **Amazon S3**: Stores processed post IDs to avoid duplicates.

---

## 📀 Extending the Project

Want to **add new news sources**? Modify `sources_registry.py`:

```python
from sources.rss_client import fetch_rss_posts
from sources.bluesky_client import fetch_bluesky_posts

def fetch_news_from_sources():
    posts = []
    posts.extend(fetch_rss_posts())
    posts.extend(fetch_bluesky_posts())
    return posts
```

---

## 🤝 Contributing

We welcome contributions! To contribute:

1. **Fork the repository**.
2. **Create a feature branch**: `git checkout -b my-feature`
3. **Make changes & commit**: `git commit -m "Added new feature"`
4. **Push to GitHub**: `git push origin my-feature`
5. **Submit a Pull Request**.

---

## 📅 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 💬 Support

Need help? **Join the Discord support server** or open a [GitHub Issue](https://github.com/YOUR_GITHUB_USERNAME/DiscordNewsBot/issues).

---

## 🚀 Star ⭐ this repo if you found it useful!

