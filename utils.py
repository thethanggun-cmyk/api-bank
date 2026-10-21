import time
import json
import urllib.parse
import urllib.request
import logging
from datetime import datetime, timezone, timedelta
from config import BOT_TOKEN, ADMIN_IDS, VN_TZ

logger = logging.getLogger("StoreBot")
USER_MESSAGE_LOG = {}
IP_VPN_CACHE = {}
IP_VPN_CACHE_TTL = 300

def lay_thoi_gian_giao_dich(item: dict) -> float:
    tran_date = str(
        item.get("transactionDate") or item.get("postingDate") or 
        item.get("tranDate") or item.get("date") or ""
    ).strip()
    pc_time = str(item.get("PCTime") or item.get("time") or "").strip()
    
    formats_to_try = [
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M",
    ]
    
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(tran_date, fmt)
            return dt.replace(tzinfo=VN_TZ).timestamp()
        except Exception:
            pass
            
    if "/" in tran_date or "-" in tran_date:
        clean_date = tran_date.split()[0]
        clean_time = pc_time
        if len(clean_time) == 6 and clean_time.isdigit():
            clean_time = f"{clean_time[:2]}:{clean_time[2:4]}:{clean_time[4:]}"
        elif not clean_time:
            clean_time = "00:00:00"
            
        combined = f"{clean_date} {clean_time}"
        for fmt in formats_to_try:
            try:
                dt = datetime.strptime(combined, fmt)
                return dt.replace(tzinfo=VN_TZ).timestamp()
            except Exception:
                pass

    return 0.0

def dinh_dang_thoi_gian(dur: str) -> str:
    d = str(dur).strip().lower()
    if d in ("1h", "1gio", "1_gio"): return "1 Giờ"
    if d in ("2h", "2gio"): return "2 Giờ"
    if d in ("3h", "3gio"): return "3 Giờ"
    if d in ("1d", "1ngay", "1_ngay", "1day"): return "1 Ngày"
    if d in ("3d", "3ngay"): return "3 Ngày"
    if d in ("7d", "7ngay", "1tuan", "1w"): return "7 Ngày (1 Tuần)"
    if d in ("15d", "15ngay"): return "15 Ngày"
    if d in ("30d", "1thang", "1month", "30ngay"): return "30 Ngày (1 Tháng)"
    if d in ("vv", "vinhvien", "permanent", "forever"): return "Vĩnh Viễn"
    if d.endswith("h"): return f"{d[:-1]} Giờ"
    if d.endswith("d"): return f"{d[:-1]} Ngày"
    if d.endswith("m") or d.endswith("thang"): return f"{d} Tháng"
    return dur if dur else "1 Ngày"

def kiem_tra_ip_vpn(ip: str) -> bool:
    global IP_VPN_CACHE
    if not ip or ip in ("127.0.0.1", "localhost"):
        return False

    now = time.time()
    cached = IP_VPN_CACHE.get(ip)
    if cached and (now - cached[1]) < IP_VPN_CACHE_TTL:
        return cached[0]

    if len(IP_VPN_CACHE) > 5000:
        IP_VPN_CACHE = {k: v for k, v in IP_VPN_CACHE.items() if (now - v[1]) < IP_VPN_CACHE_TTL}

    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode,proxy,hosting"
        req = urllib.request.Request(url, headers={"User-Agent": "SecurityGuard/3.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                is_vpn = bool(data.get("proxy") or data.get("hosting"))
                IP_VPN_CACHE[ip] = (is_vpn, now)
                return is_vpn
    except Exception as e:
        logger.warning(f"Lỗi kiểm tra VPN IP {ip}: {e}")

    IP_VPN_CACHE[ip] = (False, now)
    return False

def kiem_tra_spam(user_id: int) -> bool:
    global USER_MESSAGE_LOG
    if len(USER_MESSAGE_LOG) > 5000:
        USER_MESSAGE_LOG.clear()
    now = time.time()
    history = USER_MESSAGE_LOG.get(user_id, [])
    history = [t for t in history if now - t <= 2.0]
    history.append(now)
    USER_MESSAGE_LOG[user_id] = history
    return len(history) > 6

def gui_tin_nhan_telegram(chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN chưa được cài đặt!")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Lỗi gửi tin nhắn tới {chat_id}: {e}")
        return False

def thong_bao_cho_admin(text: str, parse_mode: str = "HTML") -> None:
    for admin_id in ADMIN_IDS:
        gui_tin_nhan_telegram(admin_id, text, parse_mode=parse_mode)
