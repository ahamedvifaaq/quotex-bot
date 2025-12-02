import asyncio
import imaplib
import email
import json
import time
import re
from email.header import decode_header
from pyquotex.stable_api import Quotex
from pyquotex.config import credentials, email_credentials

# Email Configuration
IMAP_SERVER = "imap.gmail.com"
TARGET_SUBJECT = "Alert: quotex bot"

async def connect_quotex():
    print("Fetching credentials...")
    email, password = credentials()
    print(f"Credentials obtained for email: {email}")
    
    print("Initializing Quotex client...")
    client = Quotex(email=email, password=password, lang="pt")
    
    print("Connecting to Quotex WebSocket...")
    check, message = await client.connect()
    
    if not check:
        print(f"Quotex Connection Failed: {message}")
        return None
    print("Quotex Connected Successfully!")
    return client

def clean_json_string(content):
    """
    Clean the content string to extract valid JSON.
    Finds the first '{' and the last '}' to isolate the JSON object.
    """
    try:
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            return content[start:end+1]
        return None
    except Exception:
        return None

async def process_email_signal(client, content):
    """
    Process the email content and place a trade.
    Expected content: {"symbol":"Eurusd", "side":"Buy"}
    """
    json_str = clean_json_string(content)
    if not json_str:
        print("No valid JSON found in email body.")
        return

    try:
        data = json.loads(json_str)
        symbol = data.get("symbol", "").upper()
        side = data.get("side", "").capitalize() # "Buy" or "Sell"
        
        if not symbol or not side:
            print("Invalid signal data: Missing symbol or side.")
            return

        # Map side to direction
        direction = "call" if side == "Buy" else "put" if side == "Sell" else None
        
        if not direction:
            print(f"Unknown side: {side}")
            return

        print(f"Signal Received: {symbol} - {direction.upper()}")

        # Trade Parameters (You can make these configurable)
        amount = 50
        duration = 60

        # Check asset availability
        asset_name, asset_data = await client.get_available_asset(symbol, force_open=True)
        if not asset_data[2]:
            print(f"Asset {symbol} is CLOSED. Skipping trade.")
            return

        print(f"Placing trade: {asset_name}, {direction}, {amount}, {duration}s")
        status, buy_info = await client.buy(amount, asset_name, direction, duration)
        
        if status:
            print(f"Trade Placed! ID: {buy_info['id']}")
            # Optional: Wait for result or just continue listening
        else:
            print(f"Trade Failed: {buy_info}")

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
    except Exception as e:
        print(f"Error processing signal: {e}")

async def email_listener(client):
    print("Starting Email Listener...")
    email_user, email_pass = email_credentials()
    
    while True:
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(email_user, email_pass)
            mail.select("inbox")

            # Search for UNSEEN emails with specific subject
            # Note: IMAP search criteria are a bit strict. 
            # We search for UNSEEN and filter by subject in python to be safe or use SUBJECT criteria.
            status, messages = mail.search(None, '(UNSEEN SUBJECT "Alert: quotex bot")')
            
            if status == "OK":
                email_ids = messages[0].split()
                if email_ids:
                    print(f"Found {len(email_ids)} new signal(s).")
                    
                for e_id in email_ids:
                    # Fetch the email
                    _, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")
                            
                            print(f"Processing Email: {subject}")
                            
                            # Extract Body
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    try:
                                        if content_type == "text/plain" and "attachment" not in content_disposition:
                                            body = part.get_payload(decode=True).decode()
                                            break
                                    except:
                                        pass
                            else:
                                body = msg.get_payload(decode=True).decode()

                            if body:
                                await process_email_signal(client, body)
                            else:
                                print("Empty email body.")

            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"Email Listener Error: {e}")
            # Wait a bit before retrying to avoid spamming if connection is down
            await asyncio.sleep(5)

        # Wait before next check
        await asyncio.sleep(2)

async def main():
    client = await connect_quotex()
    if not client:
        return

    # Start email listener
    # We also need to keep the websocket connection alive.
    # The client.check_connect() loop in trade_bot.py example suggests we need to maintain it.
    
    listener_task = asyncio.create_task(email_listener(client))
    
    try:
        while True:
            # Keep-alive check for Quotex
            if not await client.check_connect():
                print("Quotex connection lost. Reconnecting...")
                await client.connect()
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("Stopping bot...")
    finally:
        client.close()

import os
import threading
from flask import Flask

# Dummy Flask App for Render Web Service
app = Flask(__name__)

@app.route('/')
def home():
    return "Quotex Bot is Running!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Web Server in a separate thread
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        loop.close()
