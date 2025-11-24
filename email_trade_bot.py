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
            trade_id = buy_info['id']
            print(f"Trade Placed! ID: {trade_id}")
            
            # Log initial trade
            await log_trade({
                "id": trade_id,
                "asset": asset_name,
                "direction": direction,
                "amount": amount,
                "duration": duration,
                "status": "open",
                "result": "pending"
            })
            
            # Wait for result
            print(f"Waiting for result ({duration}s)...")
            try:
                is_win = await client.check_win(trade_id)
                
                result = "WIN" if is_win else "LOSS"
                print(f"Result: {result}")
                
                # Calculate profit (approximate based on standard payout if not available easily, 
                # but check_win usually returns bool. We can get balance to check profit or fetch payout)
                # For simplicity, let's get new balance
                new_balance = await client.get_balance()
                
                # We can try to get payout info, but for now let's estimate or just log win/loss
                # If win, profit is usually around 80-90%. Let's fetch payout.
                payout = client.get_payout_by_asset(asset_name)
                profit = (amount * payout / 100) if is_win else -amount
                
                await log_trade({
                    "id": trade_id,
                    "status": "completed",
                    "result": result,
                    "profit": profit,
                    "balance_after": new_balance
                })
                
            except Exception as e:
                print(f"Error checking result: {e}")
                
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

async def start_bot_background():
    """
    Starts the trading bot in the background.
    """
    print("Starting Trading Bot Background Task...")
    
    # Retry loop for connection
    while True:
        try:
            client = await connect_quotex()
            if client:
                # Start email listener
                listener_task = asyncio.create_task(email_listener(client))
                
                # Keep-alive loop
                while True:
                    if not await client.check_connect():
                        print("Quotex connection lost. Reconnecting...")
                        await client.connect()
                    await asyncio.sleep(10)
            else:
                print("Failed to connect to Quotex. Retrying in 30s...")
        except Exception as e:
            print(f"Bot Error: {e}")
        
        await asyncio.sleep(30)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        # For standalone testing
        loop.run_until_complete(init_db())
        loop.run_until_complete(start_bot_background())
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        loop.close()
