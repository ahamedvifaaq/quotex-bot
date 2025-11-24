import os
import sys
import json
import configparser
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"

base_dir = Path.cwd()
config_path = Path(os.path.join(base_dir, "settings/config.ini"))
config = configparser.ConfigParser(interpolation=None)


def credentials():
    # Check Environment Variables first (for Cloud/Render)
    email = os.environ.get("QUOTEX_EMAIL")
    password = os.environ.get("QUOTEX_PASS")
    
    if email and password:
        return email, password

    if not config_path.exists():
        config_path.parent.mkdir(exist_ok=True, parents=True)
        text_settings = (
            f"[settings]\n"
            f"email={input('Enter your account email: ')}\n"
            f"password={input('Enter your account password: ')}\n"
        )
        config_path.write_text(text_settings)

    config.read(config_path, encoding="utf-8")

    email = config.get("settings", "email")
    password = config.get("settings", "password")

    if not email or not password:
        print("Email and password cannot be left blank...")
        sys.exit()

    return email, password


def email_credentials():
    # Check Environment Variables first (for Cloud/Render)
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")
    
    if email_user and email_pass:
        return email_user, email_pass

    config.read(config_path, encoding="utf-8")
    
    email_user = config.get("settings", "email_user", fallback=None)
    email_pass = config.get("settings", "email_pass", fallback=None)

    if not email_user or not email_pass:
        print("\n--- Email Configuration ---")
        print("Please enter your Gmail credentials for the trading bot.")
        print("NOTE: For password, use an App Password (https://myaccount.google.com/apppasswords)")
        
        email_user = input('Enter your Gmail address: ')
        email_pass = input('Enter your Gmail App Password: ')
        
        if not config.has_section("settings"):
            config.add_section("settings")
            
        config.set("settings", "email_user", email_user)
        config.set("settings", "email_pass", email_pass)
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)

    return email_user, email_pass

def proxy():
    # Check Environment Variables first
    proxy_url = os.environ.get("QUOTEX_PROXY")
    
    if proxy_url:
        return {"http": proxy_url, "https": proxy_url}
        
    config.read(config_path, encoding="utf-8")
    proxy_url = config.get("settings", "proxy", fallback=None)
    
    if proxy_url:
        return {"http": proxy_url, "https": proxy_url}
        
    return None


def resource_path(relative_path: str | Path) -> Path:
    global base_dir
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = Path(sys._MEIPASS)
    return base_dir / relative_path


def load_session(user_agent):
    output_file = Path(
        resource_path(
            "session.json"
        )
    )
    if os.path.isfile(output_file):
        with open(output_file) as file:
            session_data = json.loads(
                file.read()
            )
    else:
        output_file.parent.mkdir(
            exist_ok=True,
            parents=True
        )
        session_dict = {
            "cookies": None,
            "token": None,
            "user_agent": user_agent
        }
        session_result = json.dumps(session_dict, indent=4)
        output_file.write_text(
            session_result
        )
        session_data = json.loads(
            session_result
        )
    return session_data


def update_session(session_data):
    output_file = Path(
        resource_path(
            "session.json"
        )
    )
    session_result = json.dumps(session_data, indent=4)
    output_file.write_text(
        session_result
    )
    session_data = json.loads(
        session_result
    )
    return session_data
