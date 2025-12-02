#!/bin/bash

# Update system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "Installing Python and Pip..."
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers (if needed by pyquotex, though simple bot might not strictly need it if using API only, but good to have)
echo "Installing Playwright browsers..."
pip install playwright
playwright install

echo "Setup complete! Don't forget to configure settings/config.ini"
