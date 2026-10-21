import os
import time
import json
import logging
import hmac
import hashlib
import urllib.parse
from datetime import timezone, timedelta

logger = logging.getLogger("StoreBot")

VN_TZ = timezone(timedelta(hours=7))

SHOP_NAME = os.getenv("SHOP_NAME", "Store").strip()
SHOP_NOTICE = os.getenv("SHOP_NOTICE", "").strip()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

WEBAPP_URL = (os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBAPP_URL") or "").strip()

BANK_CODE = os.getenv("BANK_CODE", "").strip()
BANK_ACCOUNT = os.getenv("BANK_ACCOUNT", "").strip()
BANK_ACCOUNT_NAME = os.getenv("BANK_ACCOUNT_NAME", "").strip()
BANK_PREFIX = os.getenv("BANK_PREFIX", "").strip().upper()
BANK_API_URL = os.getenv("BANK_API_URL", "").strip()
BANK_API_TOKEN = os.getenv("BANK_API_TOKEN", "").strip()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "store_data.json")
DATA_BACKUP_FILE = os.path.join(BASE_DIR, "store_data.json.bak")
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
STYLE_CSS_PATH = os.path.join(BASE_DIR, "style.css")
APP_JS_PATH = os.path.join(BASE_DIR, "app.js")

os.makedirs(UPLOAD_DIR, exist_ok=True)

DEFAULT_STORE_CONFIG = {
    "shopInfo": {
        "name": SHOP_NAME,
        "notice": SHOP_NOTICE,
        "bankCode": BANK_CODE,
        "bankAccount": BANK_ACCOUNT,
        "accountName": BANK_ACCOUNT_NAME
    },
    "bankApi": {
        "url": BANK_API_URL,
        "token": BANK_API_TOKEN,
        "prefix": BANK_PREFIX
    },
    "theme": {
        "primary": "#00e5ff",
        "secondary": "#0070f3",
        "bgBase": "#080c14",
        "bgCard": "#0e1624",
        "border": "#1a2a44"
    },
    "categories": [],
    "products": [],
    "recentTransactions": [],
    "processedTxCodes": [],
    "users": {},
    "vouchers": {},
    "giftcodes": {},
    "musicUrl": ""
}

def xac_thuc_du_lieu_telegram(init_data_raw: str, bot_token: str = None) -> dict | None:
    token = bot_token or BOT_TOKEN
    if not token or not init_data_raw:
        return None
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True))
        hash_val = parsed.pop("hash", None)
        if not hash_val:
            return None

        auth_date = int(parsed.get("auth_date", 0))
        now = int(time.time())
        if auth_date <= 0 or (now - auth_date > 7200) or (auth_date - now > 300):
            logger.warning(f"Telegram initData expired or invalid auth_date: {auth_date}")
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if hmac.compare_digest(calculated_hash, hash_val):
            user_json = parsed.get("user")
            if user_json:
                if isinstance(user_json, str):
                    return json.loads(user_json)
                return user_json
            return parsed
    except Exception as e:
        logger.error(f"Telegram initData verification error: {e}")
    return None
