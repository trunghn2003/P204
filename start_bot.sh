#!/bin/bash

# Telegram Bot Startup Script
# Usage: ./start_bot.sh

echo "🚀 Starting Telegram Bot for Google Sheets monitoring..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please configure your environment variables."
    exit 1
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json not found. Please add your Google service account credentials."
    exit 1
fi

echo "✅ Environment checks passed"
echo "🔄 Starting bot..."

# Run the bot
python advanced_bot.py
