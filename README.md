# 📰 Discord News Bot

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://github.com/jkassel/DiscordNewsBot/actions/workflows/deploy.yml/badge.svg)](https://github.com/jkassel/DiscordNewsBot/actions)
[![AWS CDK](https://img.shields.io/badge/built%20with-AWS%20CDK-orange)](https://aws.amazon.com/cdk/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)

## 🌟 Overview

**Discord News Bot** is a serverless bot that fetches **news from Bluesky and RSS feeds** and posts formatted updates to a **Discord forum or channel**. It is designed for **scalability, modularity, and ease of deployment**.

👉 **Key Features:**
- 📰 Fetches **Bluesky posts** and **RSS articles**.
- 🎨 Posts news in a **formatted Discord embed**.
- ⚡ **Serverless deployment** using **AWS Lambda** and **API Gateway**.
- 🔒 Uses **AWS Secrets Manager** for secure credential storage.
- 🛠 **Extensible design** for adding new news sources.

---

## 🛠 Prerequisite: DiscordBotShared Dependency

This bot depends on the **DiscordBotShared** repository, which contains the shared API Gateway and common infrastructure. Before deploying this bot, make sure you have:

1. Cloned and deployed the `DiscordBotShared` repository.
   ```sh
   git clone https://github.com/jkassel/DiscordBotShared.git
   cd DiscordBotShared
   cdk deploy
   ```
2. Ensure that `DiscordBotShared` exports necessary values such as the **API Gateway ID** and **endpoint**, which will be referenced in this bot.

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
git clone https://github.com/jkassel/DiscordNewsBot.git
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
EXPORT APPNAME="your_app_name"
aws secretsmanager create-secret \
    --name $APPNAME/PROD/NewsBot/DiscordSecrets \
    --secret-string '{"token": "YOUR_DISCORD_BOT_TOKEN", "webhookUrl": "YOUR_DISCORD_WEBHOOK_URL"}'
```

---

## 💬 Support

Need help? **Join the Discord support server** or open a [GitHub Issue](https://github.com/jkassel/DiscordNewsBot/issues).

---

## 🚀 Star ⭐ this repo if you found it useful!

