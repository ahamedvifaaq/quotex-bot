import asyncio
import sys
from pyquotex.stable_api import Quotex
from pyquotex.config import credentials

async def main():
    # Get credentials (will prompt if not saved)
    email, password = credentials()
    
    # Initialize client
    client = Quotex(
        email=email,
        password=password,
        lang="pt" # Default language
    )

    print("Connecting to Quotex...")
    check_connect, message = await client.connect()

    if not check_connect:
        print(f"Connection failed: {message}")
        if message == "Auth failed":
            print("Please check your email and password in settings/config.ini")
        return

    print("Connected successfully!")
    
    # Get balance
    balance = await client.get_balance()
    print(f"Current Balance: {balance}")

    # Trade parameters
    asset = "EURUSD" # You can change this
    amount = 50      # Trade amount
    direction = "call" # "call" (up) or "put" (down)
    duration = 60    # Duration in seconds

    print(f"\nPreparing to trade:")
    print(f"Asset: {asset}")
    print(f"Amount: {amount}")
    print(f"Direction: {direction}")
    print(f"Duration: {duration}s")

    # Check if asset is open
    print(f"\nChecking if {asset} is open...")
    asset_name, asset_data = await client.get_available_asset(asset, force_open=True)
    
    if not asset_data[2]:
        print(f"Asset {asset} is currently CLOSED.")
        client.close()
        return

    print(f"Asset {asset_name} is OPEN.")

    # Place trade
    print(f"\nPlacing trade...")
    status, buy_info = await client.buy(amount, asset_name, direction, duration)

    if status:
        print(f"Trade placed successfully! ID: {buy_info['id']}")
        print(f"Waiting for result ({duration}s)...")
        
        # Wait for the duration of the trade
        # In a real scenario, you might want to monitor the price or use check_win
        # Here we will just wait and check the result using the helper from examples if needed, 
        # but for simplicity we will just wait and check balance or use the check_win method if available/reliable.
        # The example uses a loop to check price, but stable_api has check_win.
        
        # Let's use check_win which seems to be designed for this
        try:
            is_win = await client.check_win(buy_info['id'])
            
            if is_win:
                print("\nResult: WIN! 🟢")
            else:
                print("\nResult: LOSS 🔴")
                
            new_balance = await client.get_balance()
            print(f"New Balance: {new_balance}")
            print(f"Profit/Loss: {new_balance - balance:.2f}")
            
        except Exception as e:
            print(f"Error checking result: {e}")

    else:
        print("Failed to place trade.")
        print(f"Details: {buy_info}")

    client.close()
    print("\nDisconnected.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        loop.close()
