#!/bin/bash

# Setup script for Telegram Bot
# Usage: ./setup.sh

echo "🛠️  Setting up Telegram Bot for Google Sheets monitoring..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "📚 Installing Python packages..."
pip install -r requirements.txt

echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy credentials.json.example to credentials.json and fill in your Google service account details"
echo "2. Copy .env and fill in your Telegram bot token and chat ID"
echo "3. Run ./start_bot.sh to start the bot"
echo ""
echo "💡 To test the setup, run: python test_bot.py"
