import os
import json
import re
import string
import random
import html
import hashlib
import mimetypes
import urllib.parse
import urllib.request
import logging
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from config import (
    BASE_DIR,
    UPLOAD_DIR,
    INDEX_HTML_PATH,
    STYLE_CSS_PATH,
    APP_JS_PATH,
    VN_TZ,
    SHOP_NAME,
    WEBAPP_URL,
    xac_thuc_du_lieu_telegram,
    ADMIN_IDS
)
from utils import (
    kiem_tra_ip_vpn,
    thong_bao_cho_admin,
    gui_tin_nhan_telegram,
    dinh_dang_thoi_gian,
    lay_thoi_gian_giao_dich
)
import time
import threading
from emoji_catalog import TG_EMOJI
from store_model import (
    tai_du_lieu_cua_hang,
    luu_du_lieu_cua_hang,
    giao_dich_du_lieu_cua_hang
)

logger = logging.getLogger("StoreBot")

_BANK_CACHE = {
    "token": "",
    "timestamp": 0.0,
    "transactions": []
}
_BANK_CACHE_LOCK = threading.Lock()

_MANUAL_DEPOSIT_NOTIFY = {}
_MANUAL_DEPOSIT_NOTIFY_LOCK = threading.Lock()

def _thong_bao_admin_duyet_tay(user_id: str, user_name: str):
    now = time.time()
    with _MANUAL_DEPOSIT_NOTIFY_LOCK:
        last_notify = _MANUAL_DEPOSIT_NOTIFY.get(user_id, 0)
        if now - last_notify < 300:
            return
        _MANUAL_DEPOSIT_NOTIFY[user_id] = now
        if len(_MANUAL_DEPOSIT_NOTIFY) > 1000:
            _MANUAL_DEPOSIT_NOTIFY.clear()
    
    thong_bao_cho_admin(
        f"{TG_EMOJI['CARD']} <b>[NẠP TIỀN - CẦN DUYỆT TAY]</b>\n"
        f"────────────────────────\n"
        f"• Khách: <b>{user_name}</b> (<code>{user_id}</code>)\n"
        f"• Bank API không khả dụng hoặc lỗi\n\n"
        f"👉 Kiểm tra app ngân hàng, sau đó dùng:\n"
        f"<code>/duyetnap {user_id} [số_tiền]</code>"
    )

_RATE_LIMIT = {}
_RATE_LIMIT_LOCK = threading.Lock()

def _kiem_tra_gioi_han_yeu_cau(ip: str, max_requests: int = 60, window: float = 60.0) -> bool:
    now = time.time()
    with _RATE_LIMIT_LOCK:
        if ip not in _RATE_LIMIT:
            _RATE_LIMIT[ip] = []
        timestamps = [t for t in _RATE_LIMIT[ip] if now - t < window]
        timestamps.append(now)
        _RATE_LIMIT[ip] = timestamps
        if len(_RATE_LIMIT) > 10000:
            _RATE_LIMIT.clear()
        return len(timestamps) > max_requests

def lay_giao_dich_ngan_hang(api_url: str, api_token: str) -> list:
    global _BANK_CACHE
    now = time.time()
    with _BANK_CACHE_LOCK:
        if _BANK_CACHE["token"] == api_token and (now - _BANK_CACHE["timestamp"]) < 4.0:
            return _BANK_CACHE["transactions"]

    target_url = api_url.replace("{token}", api_token).replace("%7Btoken%7D", api_token)
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    req = urllib.request.Request(target_url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=10) as response:
        raw_data = response.read().decode("utf-8")
        res_json = json.loads(raw_data)

    transactions = []
    if isinstance(res_json, dict):
        transactions = res_json.get("TranList") or res_json.get("transactions") or res_json.get("data") or []
    elif isinstance(res_json, list):
        transactions = res_json

    if not isinstance(transactions, list):
        transactions = []

    with _BANK_CACHE_LOCK:
        _BANK_CACHE["token"] = api_token
        _BANK_CACHE["timestamp"] = now
        _BANK_CACHE["transactions"] = transactions

    return transactions

def lay_link_webapp_chuan(params: dict = None) -> str:
    base_url = WEBAPP_URL.strip()
    if not base_url:
        logger.error("Chưa cấu hình WEBAPP_URL / RENDER_EXTERNAL_URL!")
        return ""
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = f"https://{base_url}"
    elif base_url.startswith("http://"):
        base_url = "https://" + base_url[7:]
    base_url = base_url.rstrip("/")
    if params:
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}/?{query_string}"
    return f"{base_url}/"

class SecurityHTTPHandler(SimpleHTTPRequestHandler):
    def _gui_header_bao_mat(self):
        origin = self.headers.get("Origin", "")
        allowed_origin = lay_link_webapp_chuan().rstrip("/")
        if origin and allowed_origin and origin.rstrip("/") == allowed_origin.rstrip("/"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Telegram-Init-Data")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")

    def do_OPTIONS(self):
        self.send_response(200)
        self._gui_header_bao_mat()
        self.end_headers()

    def do_GET(self):
        clean_path = self.path.split("?")[0].rstrip("/")

        if clean_path.startswith("/uploads/"):
            rel_path = clean_path[len("/uploads/"):].lstrip("/")
            file_path = os.path.abspath(os.path.join(UPLOAD_DIR, rel_path))
            upload_root = os.path.abspath(UPLOAD_DIR)

            if not file_path.startswith(upload_root) or not os.path.exists(file_path) or not os.path.isfile(file_path):
                self._gui_phan_hoi_json(404, {"error": "File not found"})
                return

            file_size = os.path.getsize(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            mime = "audio/mpeg" if ext == ".mp3" else ("image/png" if ext == ".png" else "image/jpeg")

            range_header = self.headers.get("Range")
            if range_header and range_header.startswith("bytes="):
                try:
                    ranges = range_header.replace("bytes=", "").split("-")
                    start = int(ranges[0]) if ranges[0] else 0
                    end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                    if start >= file_size:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{file_size}")
                        self.end_headers()
                        return
                    end = min(end, file_size - 1)
                    length = end - start + 1

                    self.send_response(206)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self._gui_header_bao_mat()
                    self.end_headers()

                    with open(file_path, "rb") as f:
                        f.seek(start)
                        self.wfile.write(f.read(length))
                    return
                except Exception as e:
                    logger.error(f"Lỗi stream upload: {e}")

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "public, max-age=86400")
            self._gui_header_bao_mat()
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
            return

        if clean_path in ("/style.css", "/static/css/style.css") or (clean_path.startswith("/static/") and clean_path.endswith(".css")):
            target_path = STYLE_CSS_PATH
            if os.path.exists(target_path):
                with open(target_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self._gui_header_bao_mat()
                self.end_headers()
                self.wfile.write(content)
                return

        if clean_path in ("/app.js", "/static/js/app.js") or (clean_path.startswith("/static/") and clean_path.endswith(".js")):
            target_path = APP_JS_PATH
            if os.path.exists(target_path):
                with open(target_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self._gui_header_bao_mat()
                self.end_headers()
                self.wfile.write(content)
                return

        if clean_path == "/health":
            self._gui_phan_hoi_json(200, {"status": "ok"})
            return

        if clean_path == "/api/shop-data":
            store_data = tai_du_lieu_cua_hang()
            users = store_data.get("users", {})
            top_depositors = []
            for uid, u in users.items():
                tot_dep = int(u.get("totalDeposit", 0))
                if tot_dep >= 50000:
                    top_depositors.append({
                        "id": uid,
                        "name": u.get("name") or "Khách hàng",
                        "totalDeposit": tot_dep,
                        "role": u.get("role", "customer")
                    })
            top_depositors.sort(key=lambda x: x["totalDeposit"], reverse=True)
            top_depositors = top_depositors[:10]

            sanitized = {
                "shopInfo": store_data.get("shopInfo", {}),
                "bankApi": {
                    "prefix": store_data.get("bankApi", {}).get("prefix", "")
                },
                "musicUrl": store_data.get("musicUrl", ""),
                "theme": store_data.get("theme", {}),
                "categories": store_data.get("categories", []),
                "products": [
                    {k: v for k, v in p.items() if k != "keys"}
                    for p in store_data.get("products", [])
                ],
                "recentTransactions": store_data.get("recentTransactions", []),
                "topDepositors": top_depositors
            }
            self._gui_phan_hoi_json(200, sanitized)
            return

        if clean_path == "/api/user-profile":
            init_data = self.headers.get("X-Telegram-Init-Data")
            verified_user = xac_thuc_du_lieu_telegram(init_data) if init_data else None

            if verified_user:
                uid = str(verified_user.get("id"))
            else:
                client_ip = self.client_address[0]
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                if client_ip in ("127.0.0.1", "::1") and query_params.get("preview", ["0"])[0] == "1":
                    uid = query_params.get("uid", ["0"])[0]
                else:
                    self._gui_phan_hoi_json(401, {"error": "Unauthorized"})
                    return

            store_data = tai_du_lieu_cua_hang()
            users = store_data.get("users", {})
            user_data = users.get(uid, {
                "balance": 0, "spent": 0, "totalDeposit": 0,
                "role": "customer", "inventory": [], "depositHistory": []
            })
            self._gui_phan_hoi_json(200, user_data)
            return

        if clean_path == "/api/check-security":
            client_ip = self.headers.get("CF-Connecting-IP") or self.headers.get("X-Forwarded-For") or self.client_address[0]
            if "," in client_ip:
                client_ip = client_ip.split(",")[0].strip()

            is_vpn = kiem_tra_ip_vpn(client_ip)
            self._gui_phan_hoi_json(200, {
                "vpn_detected": is_vpn,
                "ip": client_ip
            })
            return

        if clean_path in ("", "/", "/index.html", "/store"):
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if any(k in query_params for k in ("uid", "avatar", "name", "is_admin")):
                filtered_query = {k: v for k, v in query_params.items() if k not in ("uid", "avatar", "name", "is_admin")}
                redirect_target = "/"
                if filtered_query:
                    redirect_target = f"/?{urllib.parse.urlencode(filtered_query, doseq=True)}"
                self.send_response(302)
                self.send_header("Location", redirect_target)
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self._gui_header_bao_mat()
                self.end_headers()
                return

            if os.path.exists(INDEX_HTML_PATH):
                try:
                    with open(INDEX_HTML_PATH, "rb") as f:
                        content = f.read().replace(b"{{SHOP_NAME}}", html.escape(SHOP_NAME).encode("utf-8"))
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self._gui_header_bao_mat()
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logger.error(f"Lỗi gửi index.html: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._gui_header_bao_mat()
            self.end_headers()
            self.wfile.write(f"<h1>{html.escape(SHOP_NAME)} Mini App</h1>".encode("utf-8"))
            return

        self._gui_phan_hoi_json(403, {"error": "Access Denied"})

    def do_POST(self):
        MAX_BODY_SIZE = 1024 * 1024
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > MAX_BODY_SIZE:
            self._gui_phan_hoi_json(413, {"error": "Payload too large"})
            return
        clean_path = self.path.split("?")[0].rstrip("/")
        client_ip = self.client_address[0]
        if _kiem_tra_gioi_han_yeu_cau(client_ip):
            self._gui_phan_hoi_json(429, {"error": "Too many requests"})
            return

        if clean_path == "/api/notify-activity":
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                init_data = self.headers.get("X-Telegram-Init-Data")
                verified_user = xac_thuc_du_lieu_telegram(init_data) if init_data else None
                if not verified_user:
                    self._gui_phan_hoi_json(401, {"error": "Unauthorized"})
                    return
                act_type = payload.get("type", "unknown")
                u_id = str(payload.get("user_id", "0"))
                u_name = html.escape(str(payload.get("user_name", "Khách hàng")))
                now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

                if act_type == "open_app":
                    thong_bao_cho_admin(
                        f"{TG_EMOJI['ROCKET']} <b>[HOẠT ĐỘNG] KHÁCH MỞ CỬA HÀNG</b>\n"
                        f"────────────────────────\n"
                        f"• Người dùng: <b>{u_name}</b> (<code>{u_id}</code>)\n"
                        f"• Thời gian: <code>{now_str}</code>"
                    )
                elif act_type == "view_deposit":
                    thong_bao_cho_admin(
                        f"{TG_EMOJI['CARD']} <b>[HOẠT ĐỘNG] KHÁCH VÀO TAB NẠP TIỀN</b>\n"
                        f"────────────────────────\n"
                        f"• Người dùng: <b>{u_name}</b> (<code>{u_id}</code>)\n"
                        f"• Đang xem mã VietQR MBBank tự động."
                    )
                self._gui_phan_hoi_json(200, {"success": True})
            except Exception as e:
                self._gui_phan_hoi_json(500, {"success": False, "message": "Lỗi xử lý yêu cầu."})
            return

        if clean_path == "/api/purchase":
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                init_data = self.headers.get("X-Telegram-Init-Data")
                verified_user = xac_thuc_du_lieu_telegram(init_data) if init_data else None

                if not verified_user:
                    self._gui_phan_hoi_json(401, {
                        "success": False,
                        "message": "Phiên làm việc Telegram không hợp lệ hoặc đã hết hạn! Vui lòng mở lại từ Telegram Bot."
                    })
                    return

                uid = str(verified_user.get("id"))
                prod_id = payload.get("prod_id")
                raw_user_name = verified_user.get("first_name") or str(payload.get("user_name", "Khách hàng"))
                user_name = html.escape(str(raw_user_name)[:50])

                delivered_key = None
                user_record_snapshot = None
                prod_name = ""
                duration_label = ""
                effective_price = 0
                price_type_label = ""
                stock_left = 0

                with giao_dich_du_lieu_cua_hang() as current_data:
                    users = current_data.setdefault("users", {})
                    user_record = users.setdefault(uid, {
                        "balance": 0, "spent": 0, "totalDeposit": 0, "role": "customer", "inventory": [], "depositHistory": []
                    })

                    prod = next((p for p in current_data.get("products", []) if p.get("id") == prod_id), None)
                    if not prod:
                        self._gui_phan_hoi_json(400, {"success": False, "message": "Sản phẩm không tồn tại!"})
                        return

                    keys_list = prod.get("keys", [])
                    if prod.get("stock", 0) <= 0 or not keys_list:
                        self._gui_phan_hoi_json(400, {"success": False, "message": "Sản phẩm đã hết hàng trong kho!"})
                        return

                    is_seller = (user_record.get("role") == "seller")
                    seller_price = int(prod.get("sellerPrice") or 0)
                    regular_price = int(prod.get("price", 0))

                    effective_price = regular_price
                    price_type_label = "Giá Khách Lẻ"
                    if is_seller and seller_price > 0:
                        effective_price = seller_price
                        price_type_label = "Giá Seller VIP"

                    if user_record["balance"] < effective_price:
                        self._gui_phan_hoi_json(400, {
                            "success": False,
                            "message": f"Số dư không đủ! Cần {effective_price:,}đ. Vui lòng nạp thêm."
                        })
                        return

                    delivered_key = keys_list.pop(0)
                    prod["stock"] = len(keys_list)
                    stock_left = prod["stock"]

                    user_record["balance"] -= effective_price
                    user_record["spent"] += effective_price

                    duration_label = dinh_dang_thoi_gian(prod.get("duration", "1d"))
                    now_time = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
                    prod_name = html.escape(str(prod.get('name', '')))

                    user_record.setdefault("inventory", []).insert(0, {
                        "productName": f"{prod.get('name')} ({duration_label})",
                        "secretKey": delivered_key,
                        "time": now_time
                    })

                    current_data.setdefault("recentTransactions", []).insert(0, {
                        "name": user_name,
                        "type": "mua",
                        "amount": effective_price,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    current_data["recentTransactions"] = current_data["recentTransactions"][:15]

                    user_record_snapshot = {
                        "balance": user_record["balance"],
                        "spent": user_record["spent"]
                    }

                if uid.isdigit():
                    gui_tin_nhan_telegram(
                        int(uid),
                        f"{TG_EMOJI['GIFT']} <b>GIAO DỊCH MUA KEY THÀNH CÔNG!</b>\n"
                        f"────────────────────────\n"
                        f"• Sản phẩm: <b>{prod_name}</b>\n"
                        f"• Thời hạn: <b>{duration_label}</b>\n"
                        f"• Mức giá: <b>{effective_price:,} VNĐ</b> ({price_type_label})\n"
                        f"• Số dư còn lại: <b>{user_record_snapshot['balance']:,} VNĐ</b>\n\n"
                        f"{TG_EMOJI['KEY']} <b>MÃ KEY CỦA BẠN:</b>\n"
                        f"<code>{html.escape(delivered_key)}</code>\n\n"
                        f"📌 <i>Mã này được lưu vĩnh viễn trong tin nhắn này.</i>"
                    )

                thong_bao_cho_admin(
                    f"{TG_EMOJI['SHOPPING']} <b>[ĐƠN HÀNG MỚI] BÁN KEY THÀNH CÔNG!</b>\n"
                    f"────────────────────────\n"
                    f"• Khách: <b>{user_name}</b> (<code>{uid}</code>)\n"
                    f"• Sản phẩm: <b>{prod_name}</b> ({duration_label})\n"
                    f"• Thu về: <b>{effective_price:,} VNĐ</b> ({price_type_label})\n"
                    f"• Key cấp: <code>{html.escape(delivered_key)}</code>\n"
                    f"• Tồn kho còn lại: <b>{stock_left}</b>"
                )

                self._gui_phan_hoi_json(200, {
                    "success": True,
                    "key": delivered_key,
                    "balance": user_record_snapshot["balance"],
                    "spent": user_record_snapshot["spent"]
                })
            except Exception as e:
                logger.error(f"Lỗi mua hàng: {e}")
                self._gui_phan_hoi_json(500, {"success": False, "message": "Lỗi hệ thống, vui lòng thử lại sau."})
            return

        if clean_path == "/api/check-deposit":
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
                init_data = self.headers.get("X-Telegram-Init-Data")
                verified_user = xac_thuc_du_lieu_telegram(init_data) if init_data else None

                if not verified_user:
                    self._gui_phan_hoi_json(401, {"success": False, "message": "Phiên làm việc Telegram không hợp lệ!"})
                    return

                user_id = str(verified_user.get("id"))
                raw_user_name = verified_user.get("first_name") or str(data.get("user_name", "Khách hàng"))
                user_name = html.escape(str(raw_user_name)[:50])

                store_data = tai_du_lieu_cua_hang()
                api_url = store_data.get("bankApi", {}).get("url", "")
                api_token = store_data.get("bankApi", {}).get("token", "").strip()
                bank_prefix = store_data.get("bankApi", {}).get("prefix", "").strip().upper()

                min_amount = int(data.get("amount", 1000))
                if min_amount < 1000:
                    min_amount = 1000

                if not api_token or not api_url or not bank_prefix:
                    _thong_bao_admin_duyet_tay(user_id, user_name)
                    self._gui_phan_hoi_json(200, {
                        "success": False,
                        "manual_mode": True,
                        "message": "Hệ thống nạp tự động chưa sẵn sàng. Admin sẽ duyệt nạp tiền thủ công cho bạn. Dùng lệnh /duyetnap trong bot."
                    })
                    return

                try:
                    transactions = lay_giao_dich_ngan_hang(api_url, api_token)
                except Exception as bank_err:
                    logger.error(f"Bank API error: {bank_err}")
                    _thong_bao_admin_duyet_tay(user_id, user_name)
                    self._gui_phan_hoi_json(200, {
                        "success": False,
                        "manual_mode": True,
                        "message": "Cổng ngân hàng tạm lỗi. Admin đã được thông báo và sẽ duyệt nạp tiền thủ công."
                    })
                    return

                if not transactions:
                    self._gui_phan_hoi_json(200, {
                        "success": False,
                        "message": "Chưa có biến động số dư nào từ ngân hàng."
                    })
                    return

                matched_transaction = None
                clean_user_id = re.sub(r"[^0-9]", "", user_id).strip()
                now_ts = datetime.now(VN_TZ).timestamp()
                processed_set = set(store_data.get("processedTxCodes", []))

                for item in transactions:
                    if not isinstance(item, dict):
                        continue

                    credit_amt_raw = str(item.get("creditAmount") or item.get("Amount") or "0").replace(",", "").replace(".", "").strip()
                    debit_amt_raw = str(item.get("debitAmount") or "0").replace(",", "").replace(".", "").strip()

                    try:
                        amount_val = int(credit_amt_raw)
                    except ValueError:
                        amount_val = 0

                    is_credit = False
                    if amount_val > 0 and (debit_amt_raw == "0" or not debit_amt_raw):
                        is_credit = True

                    if is_credit and amount_val >= min_amount:
                        tx_ts = lay_thoi_gian_giao_dich(item)
                        if tx_ts > 0:
                            time_diff = now_ts - tx_ts
                            if time_diff > 900.0 or time_diff < -180.0:
                                continue

                        desc = (str(item.get("description", "")) + " " + str(item.get("Description", "")) + " " + str(item.get("Remark", ""))).upper()
                        clean_desc = re.sub(r"[^A-Z0-9]", "", desc)

                        if bank_prefix not in clean_desc:
                            continue

                        ref_no = str(item.get("refNo") or item.get("tranId") or "").strip()
                        tx_date = str(item.get("transactionDate") or item.get("postingDate") or "").strip()

                        ref_id = f"{tx_date}_{ref_no}_{amount_val}" if ref_no else f"MB_{hashlib.sha256(desc.encode()).hexdigest()[:16]}_{amount_val}"

                        if ref_id in processed_set:
                            continue

                        if clean_user_id and clean_user_id in clean_desc:
                            matched_transaction = {
                                "tx_id": ref_id,
                                "amount": amount_val,
                                "description": desc,
                                "time": tx_date or datetime.now().strftime("%H:%M:%S")
                            }
                            break

                if matched_transaction:
                    now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
                    new_balance = 0

                    with giao_dich_du_lieu_cua_hang() as current_store:
                        cur_processed = set(current_store.setdefault("processedTxCodes", []))
                        if matched_transaction["tx_id"] in cur_processed:
                            self._gui_phan_hoi_json(200, {
                                "success": True,
                                "message": "Giao dịch đã được cập nhật thành công!"
                            })
                            return

                        current_store["processedTxCodes"].append(matched_transaction["tx_id"])
                        users = current_store.setdefault("users", {})
                        user_record = users.setdefault(user_id, {
                            "balance": 0, "spent": 0, "totalDeposit": 0, "role": "customer", "inventory": [], "depositHistory": []
                        })
                        user_record["balance"] += matched_transaction["amount"]
                        user_record["totalDeposit"] += matched_transaction["amount"]
                        new_balance = user_record["balance"]

                        user_record.setdefault("depositHistory", []).insert(0, {
                            "method": "VietQR MBBank Auto 24/7",
                            "amount": matched_transaction["amount"],
                            "status": "Thành công",
                            "time": now_str
                        })

                        current_recent = current_store.setdefault("recentTransactions", [])
                        current_recent.insert(0, {
                            "name": user_name,
                            "type": "nạp",
                            "amount": matched_transaction["amount"],
                            "time": datetime.now().strftime("%H:%M")
                        })
                        current_store["recentTransactions"] = current_recent[:15]

                    if user_id.isdigit():
                        gui_tin_nhan_telegram(
                            int(user_id),
                            f"{TG_EMOJI['FIRE']} <b>NẠP TIỀN THÀNH CÔNG!</b>\n"
                            f"────────────────────────\n"
                            f"• Số tiền: <b>+{matched_transaction['amount']:,} VNĐ</b>\n"
                            f"• Số dư mới: <b>{new_balance:,} VNĐ</b>\n"
                            f"• Mã GD: <code>{matched_transaction['tx_id']}</code>\n"
                            f"• Thời gian: <code>{now_str}</code>\n\n"
                            f"Số dư đã được cập nhật!"
                        )

                    thong_bao_cho_admin(
                        f"{TG_EMOJI['MONEY']} <b>[AUTO BANK THẬT] NẠP THÀNH CÔNG!</b>\n"
                        f"────────────────────────\n"
                        f"• Khách nạp: <b>{user_name}</b> (<code>{user_id}</code>)\n"
                        f"• Thực nhận: <b>+{matched_transaction['amount']:,} VNĐ</b>\n"
                        f"• Mã GD: <code>{matched_transaction['tx_id']}</code>\n"
                        f"• Số dư tài khoản: <b>{new_balance:,} VNĐ</b>"
                    )

                    self._gui_phan_hoi_json(200, {
                        "success": True,
                        "amount": matched_transaction["amount"],
                        "balance": new_balance,
                        "tx_id": matched_transaction["tx_id"],
                        "message": f"Nạp thành công +{matched_transaction['amount']:,}đ!"
                    })
                else:
                    self._gui_phan_hoi_json(200, {
                        "success": False,
                        "message": "Chưa phát hiện biến động số dư ngân hàng hợp lệ."
                    })

            except Exception as e:
                logger.error(f"Lỗi API Bank: {e}")
                _thong_bao_admin_duyet_tay(user_id if 'user_id' in dir() else '0', user_name if 'user_name' in dir() else 'Unknown')
                self._gui_phan_hoi_json(200, {
                    "success": False,
                    "manual_mode": True,
                    "message": "Cổng ngân hàng tạm lỗi. Admin đã được thông báo."
                })
            return

        if clean_path == "/api/redeem-code":
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                init_data = self.headers.get("X-Telegram-Init-Data")
                verified_user = xac_thuc_du_lieu_telegram(init_data) if init_data else None

                if not verified_user:
                    self._gui_phan_hoi_json(401, {"success": False, "message": "Phiên làm việc Telegram không hợp lệ!"})
                    return

                user_id = str(verified_user.get("id"))
                code = str(payload.get("code", "")).strip().upper()
                code_type = payload.get("type", "voucher")
                now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
                resp_msg = ""
                balance_after = 0
                inventory_after = []

                with giao_dich_du_lieu_cua_hang() as current_data:
                    users = current_data.setdefault("users", {})
                    user_record = users.setdefault(user_id, {
                        "balance": 0, "spent": 0, "totalDeposit": 0, "role": "customer", "inventory": [], "depositHistory": []
                    })

                    code_map = current_data.get("vouchers", {}) if code_type == "voucher" else current_data.get("giftcodes", {})

                    if code not in code_map:
                        self._gui_phan_hoi_json(400, {"success": False, "message": f"Mã {code_type.upper()} không tồn tại hoặc đã hết hạn!"})
                        return

                    item = code_map[code]
                    used_by = item.setdefault("usedBy", [])
                    if user_id in used_by:
                        self._gui_phan_hoi_json(400, {"success": False, "message": "Bạn đã sử dụng mã này rồi!"})
                        return

                    used_by.append(user_id)

                    if item.get("type") == "balance":
                        add_amt = int(item.get("amount", 0))
                        user_record["balance"] += add_amt
                        user_record.setdefault("depositHistory", []).insert(0, {
                            "method": f"Mã {code_type.capitalize()}: {code}",
                            "amount": add_amt,
                            "status": "Thành công",
                            "time": now_str
                        })
                        resp_msg = f"Đã áp dụng mã thành công: +{add_amt:,} VNĐ!"
                    elif item.get("type") == "key":
                        p_name = item.get("productName", "Vật Phẩm Giftcode")
                        p_key = item.get("key", "")
                        user_record.setdefault("inventory", []).insert(0, {
                            "productName": p_name,
                            "secretKey": p_key,
                            "time": now_str
                        })
                        resp_msg = f"Chúc mừng bạn nhận được {p_name}!"
                        if user_id.isdigit():
                            gui_tin_nhan_telegram(int(user_id), f"{TG_EMOJI['GIFT']} <b>QUÀ TẶNG GIFTCODE:</b>\n• Tên quà: <b>{html.escape(p_name)}</b>\n• Key: <code>{html.escape(p_key)}</code>")

                    balance_after = user_record["balance"]
                    inventory_after = user_record.get("inventory", [])

                thong_bao_cho_admin(
                    f"{TG_EMOJI['GIFT']} <b>[KHÁCH SỬ DỤNG {code_type.upper()}]</b>\n"
                    f"────────────────────────\n"
                    f"• Khách: <code>{user_id}</code>\n"
                    f"• Mã: <code>{html.escape(code)}</code>\n"
                    f"• Kết quả: {html.escape(resp_msg)}"
                )

                self._gui_phan_hoi_json(200, {
                    "success": True,
                    "message": resp_msg,
                    "balance": balance_after,
                    "inventory": inventory_after
                })
            except Exception as e:
                self._gui_phan_hoi_json(500, {"success": False, "message": "Lỗi hệ thống, vui lòng thử lại sau."})
            return

        self._gui_phan_hoi_json(403, {"error": "Access Denied"})

    def _gui_phan_hoi_json(self, code: int, payload: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._gui_header_bao_mat()
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
