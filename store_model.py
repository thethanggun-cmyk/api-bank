import os
import json
import copy
import random
import shutil
import logging
import threading
from contextlib import contextmanager
from config import (
    DATA_FILE, DATA_BACKUP_FILE, DEFAULT_STORE_CONFIG,
    SHOP_NAME, SHOP_NOTICE, BANK_CODE, BANK_ACCOUNT, BANK_ACCOUNT_NAME,
    BANK_PREFIX, BANK_API_URL, BANK_API_TOKEN
)

logger = logging.getLogger("StoreBot")
_DATA_LOCK = threading.RLock()
_ENV_SHOP_KEYS = ("name", "bankCode", "bankAccount", "accountName")

def _doc_du_lieu_noi_bo() -> dict:
    data = None
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Lỗi đọc {DATA_FILE}: {e}")
            if os.path.exists(DATA_BACKUP_FILE):
                try:
                    with open(DATA_BACKUP_FILE, "r", encoding="utf-8") as bf:
                        data = json.load(bf)
                except Exception as be:
                    logger.error(f"Lỗi đọc backup: {be}")

    if not data:
        data = copy.deepcopy(DEFAULT_STORE_CONFIG)

    if not isinstance(data.get("processedTxCodes"), list):
        data["processedTxCodes"] = []
    if not isinstance(data.get("users"), dict):
        data["users"] = {}
    if not isinstance(data.get("categories"), list):
        data["categories"] = []
    if not isinstance(data.get("products"), list):
        data["products"] = []
    if not isinstance(data.get("vouchers"), dict):
        data["vouchers"] = copy.deepcopy(DEFAULT_STORE_CONFIG["vouchers"])
    if not isinstance(data.get("giftcodes"), dict):
        data["giftcodes"] = copy.deepcopy(DEFAULT_STORE_CONFIG["giftcodes"])
    if "musicUrl" not in data:
        data["musicUrl"] = ""

    data.pop("uiText", None)

    shop = data.setdefault("shopInfo", {})
    shop["name"] = SHOP_NAME
    shop["bankCode"] = BANK_CODE
    shop["bankAccount"] = BANK_ACCOUNT
    shop["accountName"] = BANK_ACCOUNT_NAME
    shop.setdefault("notice", SHOP_NOTICE)

    bank = data.setdefault("bankApi", {})
    bank["url"] = BANK_API_URL
    bank["token"] = BANK_API_TOKEN
    bank["prefix"] = BANK_PREFIX

    return data

def _luu_du_lieu_noi_bo(data: dict) -> bool:
    if isinstance(data.get("processedTxCodes"), list) and len(data["processedTxCodes"]) > 1000:
        data["processedTxCodes"] = data["processedTxCodes"][-1000:]

    to_save = dict(data)
    to_save["shopInfo"] = {k: v for k, v in data.get("shopInfo", {}).items() if k not in _ENV_SHOP_KEYS}
    to_save.pop("bankApi", None)

    temp_file = f"{DATA_FILE}.tmp_{random.randint(1000, 9999)}"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
        if os.path.exists(DATA_FILE):
            shutil.copyfile(DATA_FILE, DATA_BACKUP_FILE)
        os.replace(temp_file, DATA_FILE)
        return True
    except Exception as e:
        logger.error(f"Lỗi lưu file {DATA_FILE}: {e}")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return False

def tai_du_lieu_cua_hang() -> dict:
    with _DATA_LOCK:
        return _doc_du_lieu_noi_bo()

def luu_du_lieu_cua_hang(data: dict) -> bool:
    with _DATA_LOCK:
        return _luu_du_lieu_noi_bo(data)

@contextmanager
def giao_dich_du_lieu_cua_hang():
    with _DATA_LOCK:
        data = _doc_du_lieu_noi_bo()
        _commit = True
        try:
            yield data
        except Exception:
            _commit = False
            raise
        finally:
            if _commit:
                _luu_du_lieu_noi_bo(data)
