import os
import html
import time
import random
import re
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from config import ADMIN_IDS, UPLOAD_DIR, SHOP_NAME, BANK_ACCOUNT, BANK_ACCOUNT_NAME, BANK_PREFIX
from utils import kiem_tra_spam, gui_tin_nhan_telegram, dinh_dang_thoi_gian
from emoji_catalog import TG_EMOJI
from server_handler import lay_link_webapp_chuan
from store_model import tai_du_lieu_cua_hang, luu_du_lieu_cua_hang

logger = logging.getLogger("StoreBot")
SHOP_TITLE = html.escape(SHOP_NAME).upper()
WAITING_PHOTO_USERS = set()
WAITING_MUSIC_USERS = set()

async def lenh_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if kiem_tra_spam(user_id):
        return

    try:
        store_data = tai_du_lieu_cua_hang()
        users = store_data.setdefault("users", {})
        uid_str = str(user_id)
        if uid_str not in users:
            users[uid_str] = {
                "balance": 0, "spent": 0, "totalDeposit": 0, "inventory": [], "depositHistory": [],
                "role": "customer",
                "name": user.first_name or "Khách hàng",
                "username": user.username or "",
                "joined_at": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            luu_du_lieu_cua_hang(store_data)
    except Exception as e:
        logger.error(f"Lỗi cập nhật người dùng: {e}")

    try:
        if update.message:
            await update.message.delete()
    except Exception:
        pass

    first_name = html.escape(user.first_name or "Khách hàng")
    client_mini_app = lay_link_webapp_chuan()

    welcome_text = (
        f"{TG_EMOJI['LIGHTNING']} <b>HỆ THỐNG DỊCH VỤ TỰ ĐỘNG - {SHOP_TITLE}</b>\n"
        f"────────────────────────\n"
        f"Chào <b>{first_name}</b>, hệ thống đã đồng bộ.\n\n"
        f"📱 <code>/nap</code> : Nạp tiền VietQR MBBank tự động 24/7 (1s)\n"
        f"📦 <code>/ds</code> : Xem danh mục & sản phẩm đang mở bán\n"
        f"🔑 <code>/kho</code> : Xem lại toàn bộ key đã mua\n"
        f"👤 <code>/me</code> : Kiểm tra số dư & thông tin tài khoản\n"
        f"🏆 <code>/top</code> : Bảng xếp hạng nạp tiền (Tối thiểu 50k)"
    )

    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🚀 MỞ CỬA HÀNG (MINI APP)",
                web_app=WebAppInfo(url=client_mini_app)
            )
        ],
        [
            InlineKeyboardButton(text="🛒 Mua Key", callback_data="btn_open_shop"),
            InlineKeyboardButton(text="🔑 Kho Key", callback_data="btn_my_keys")
        ],
        [
            InlineKeyboardButton(text="💳 Nạp Tiền MBBank", callback_data="btn_deposit_info"),
            InlineKeyboardButton(text="👤 Số Dư", callback_data="btn_check_account")
        ]
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )

async def lenh_kho(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    store_data = tai_du_lieu_cua_hang()
    user_rec = store_data.get("users", {}).get(str(user_id), {})
    inventory = user_rec.get("inventory", [])

    if not inventory:
        await update.effective_message.reply_text(
            f"{TG_EMOJI['SHOPPING']} <b>KHO HÀNG CỦA BẠN:</b>\nBạn chưa mua sản phẩm nào. Hãy mở Mini App hoặc gõ <code>/ds</code> để mua hàng!",
            parse_mode="HTML"
        )
        return

    msg = f"{TG_EMOJI['KEY']} <b>KHO KEY CỦA BẠN ({len(inventory)} sản phẩm):</b>\n────────────────────────\n"
    for i, item in enumerate(inventory[:15], 1):
        msg += f"{i}. <b>{item.get('productName')}</b> (<code>{item.get('time', '')}</code>)\n"
        msg += f"   👉 Mã Key: <code>{item.get('secretKey')}</code>\n\n"

    msg += "<i>(Chạm vào mã key bất kỳ để sao chép trực tiếp)</i>"
    await update.effective_message.reply_text(msg, parse_mode="HTML")

async def lenh_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    store_data = tai_du_lieu_cua_hang()
    u = store_data.get("users", {}).get(str(user_id), {})
    bal = u.get("balance", 0)
    role = u.get("role", "customer")
    role_name = "⭐ Seller VIP" if role == "seller" else ("👑 Admin" if user_id in ADMIN_IDS else "Khách Hàng")
    await update.effective_message.reply_text(
        f"{TG_EMOJI['USER']} <b>THÔNG TIN TÀI KHOẢN:</b>\n"
        f"────────────────────────\n"
        f"• Họ tên: <b>{user.first_name}</b>\n"
        f"• Telegram ID: <code>{user_id}</code>\n"
        f"• Cấp bậc: <b>{role_name}</b>\n"
        f"• Số dư: <b>{bal:,} VNĐ</b>\n"
        f"• Tổng đã nạp: <b>{u.get('totalDeposit', 0):,} VNĐ</b>\n"
        f"• Đã mua: <b>{len(u.get('inventory', []))} sản phẩm</b>",
        parse_mode="HTML"
    )

async def lenh_nap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    client_mini_app = lay_link_webapp_chuan()
    await update.effective_message.reply_text(
        f"{TG_EMOJI['CARD']} <b>NẠP TIỀN AUTO MBBANK (MB) 24/7:</b>\n\n"
        f"Mở Mini App để quét mã VietQR tự động đối soát trong 1 giây:\n"
        f"• Ngân hàng: <b>MB (MBBank)</b>\n"
        f"• STK: <code>{BANK_ACCOUNT}</code>\n"
        f"• Chủ TK: <b>{BANK_ACCOUNT_NAME}</b>\n"
        f"• Cú pháp: <code>{BANK_PREFIX} {user_id}</code>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Mở Nạp Tiền (Mini App)", web_app=WebAppInfo(url=client_mini_app))
        ]]),
        parse_mode="HTML"
    )

async def lenh_ds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store_data = tai_du_lieu_cua_hang()
    prods = store_data.get("products", [])
    if not prods:
        await update.message.reply_text("📦 Hiện tại chưa có sản phẩm nào được đăng bán.")
        return

    msg = f"{TG_EMOJI['SHOPPING']} <b>DANH SÁCH SẢN PHẨM TRÊN HỆ THỐNG:</b>\n────────────────────────\n"
    for p in prods:
        dur = dinh_dang_thoi_gian(p.get("duration", "1d"))
        msg += f"• <b>{p.get('name')}</b> ({dur})\n"
        msg += f"  ID: <code>{p.get('id')}</code> | Mục: <code>{p.get('categoryId')}</code>\n"
        msg += f"  Giá lẻ: <code>{p.get('price', 0):,}đ</code> | Seller: <code>{p.get('sellerPrice', 0):,}đ</code>\n"
        msg += f"  Tồn kho: <b>{p.get('stock', 0)} key</b>\n\n"

    await update.message.reply_text(msg, parse_mode="HTML")

async def lenh_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store_data = tai_du_lieu_cua_hang()
    users = store_data.get("users", {})
    eligible = [
        (uid, info) for uid, info in users.items()
        if int(info.get("totalDeposit", 0)) >= 50000
    ]
    eligible.sort(key=lambda x: int(x[1].get("totalDeposit", 0)), reverse=True)
    top_5 = eligible[:5]

    msg = f"{TG_EMOJI['TROPHY']} <b>BẢNG XẾP HẠNG TOP NẠP (TỐI THIỂU 50.000 VNĐ):</b>\n────────────────────────\n"
    if not top_5:
        msg += "Chưa có thành viên nào đạt mốc nạp từ 50.000 VNĐ trở lên."
    else:
        for i, (uid, info) in enumerate(top_5, 1):
            role_icon = "⭐ " if info.get("role") == "seller" else ""
            msg += f"{i}. <b>{info.get('name', 'Khách')}</b> {role_icon}(<code>{uid}</code>): <code>{info.get('totalDeposit', 0):,} VNĐ</code>\n"

    await update.message.reply_text(msg, parse_mode="HTML")

async def lenh_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Bạn không có quyền Quản trị viên!")
        return

    help_msg = (
        f"{TG_EMOJI['CROWN']} <b>BẢNG LỆNH QUẢN TRỊ VIÊN - {SHOP_TITLE}</b>\n"
        "────────────────────────\n"
        "📦 <b>1. QUẢN LÝ SẢN PHẨM & TÀI KHOẢN:</b>\n"
        "• <code>/themsp Tên | Mã_Game | Thời_hạn | Giá_lẻ | Giá_seller | Key1,Key2... | [key hoặc acc]</code>\n"
        "• <code>/nhapkey &lt;Mã_SP&gt; &lt;Key1, Key2... hoặc xuống dòng&gt;</code>\n"
        "• <code>/xoasp &lt;Mã_SP&gt;</code> : Xoá vĩnh viễn sản phẩm\n"
        "• <code>/dssp</code> : Liệt kê tất cả sản phẩm & tồn kho key\n"
        "• <code>/khokey</code> : Xem toàn bộ kho key của tất cả sản phẩm\n\n"
        "📁 <b>2. QUẢN LÝ DANH MỤC GAME:</b>\n"
        "• <code>/themdanhmuc &lt;id&gt; | &lt;Tên&gt; | &lt;Icon&gt;</code>\n"
        "• <code>/xoadanhmuc &lt;id&gt;</code> : Xoá danh mục\n"
        "• <code>/dsdanhmuc</code> : Liệt kê toàn bộ danh mục game\n\n"
        "👥 <b>3. QUẢN LÝ THÀNH VIÊN &amp; SELLER:</b>\n"
        "• <code>/setvip &lt;Telegram_ID&gt; &lt;seller|customer&gt;</code> : Nâng/Hạ bậc Seller VIP\n"
        "• <code>/congtien &lt;Telegram_ID&gt; &lt;Số_tiền&gt;</code> : Cộng tiền tài khoản\n"
        "• <code>/trutien &lt;Telegram_ID&gt; &lt;Số_tiền&gt;</code> : Trừ tiền tài khoản\n"
        "• <code>/duyetnap &lt;Telegram_ID&gt; &lt;Số_tiền&gt;</code> : Duyệt nạp tiền thủ công\n"
        "• <code>/thanhvien</code> : Xem danh sách thành viên &amp; số dư\n\n"
        "⚙️ <b>4. CÀI ĐẶT SHOP &amp; HỆ THỐNG:</b>\n"
        "• <code>/addmusic</code> : Gửi nhạc nền tự phát cho Mini App\n"
        "• <code>/taolink</code> : Gửi ảnh lấy link ảnh HTTPS trực tiếp\n"
        "• <code>/thongbao &lt;Nội_dung&gt;</code> : Phát thông báo tới toàn bộ khách\n"
        "• <code>/caidat</code> : Xem và đổi thông báo shop"
    )
    await update.effective_message.reply_text(help_msg, parse_mode="HTML")

async def lenh_them_san_pham(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    raw_text = (update.effective_message.text or "").split(None, 1)
    if len(raw_text) < 2 or "|" not in raw_text[1]:
        await update.effective_message.reply_text(
            f"{TG_EMOJI['WARNING']} <b>CÚ PHÁP THÊM SẢN PHẨM:</b>\n"
            "<code>/themsp Tên sản phẩm | Mã Game | Thời hạn | Giá lẻ | Giá Seller VIP | Key1, Key2... | [key hoặc acc]</code>\n\n"
            "👉 <b>Ví dụ (Key):</b>\n"
            "<code>/themsp Tool Aim V1 | freefire | 1d | 30000 | 20000 | KEY-A1, KEY-A2 | key</code>\n\n"
            "👉 <b>Ví dụ (Tài khoản):</b>\n"
            "<code>/themsp Acc FF Rank KC | freefire | vv | 150000 | 120000 | tk1:mk1, tk2:mk2 | acc</code>",
            parse_mode="HTML"
        )
        return

    parts = [p.strip() for p in raw_text[1].split("|")]
    if len(parts) < 5:
        await update.effective_message.reply_text(f"{TG_EMOJI['CROSS']} Thiếu thông tin! Cần ít nhất 5 phần: Tên | Mã Game | Thời hạn | Giá lẻ | Giá Seller", parse_mode="HTML")
        return

    name = parts[0]
    cat_id = parts[1].lower()
    duration = parts[2].lower()
    try:
        price = int(re.sub(r"[^\d]", "", parts[3]))
        seller_price = int(re.sub(r"[^\d]", "", parts[4]))
    except Exception:
        await update.effective_message.reply_text(f"{TG_EMOJI['CROSS']} Giá bán không hợp lệ!", parse_mode="HTML")
        return

    keys = []
    if len(parts) >= 6 and parts[5]:
        keys = [k.strip() for k in re.split(r"[\n,]+", parts[5]) if k.strip()]

    prod_type = "key"
    if len(parts) >= 7 and parts[6].lower() in ("acc", "account", "tai_khoan", "taikhoan"):
        prod_type = "acc"

    store_data = tai_du_lieu_cua_hang()
    prod_id = f"p_{int(time.time())}_{random.randint(100, 999)}"

    new_prod = {
        "id": prod_id,
        "name": name,
        "categoryId": cat_id,
        "duration": duration,
        "type": prod_type,
        "price": price,
        "sellerPrice": seller_price,
        "stock": len(keys),
        "keys": keys
    }

    store_data.setdefault("products", []).append(new_prod)
    luu_du_lieu_cua_hang(store_data)

    dur_text = dinh_dang_thoi_gian(duration)
    type_label = "📦 Gói Key" if prod_type == "key" else "👤 Kho Tài Khoản (Acc)"
    await update.effective_message.reply_text(
        f"{TG_EMOJI['CHECK']} <b>ĐÃ THÊM SẢN PHẨM THÀNH CÔNG!</b>\n"
        f"────────────────────────\n"
        f"• Loại: <b>{type_label}</b>\n"
        f"• Mã ID: <code>{prod_id}</code>\n"
        f"• Tên SP: <b>{name}</b>\n"
        f"• Danh mục: <code>{cat_id}</code>\n"
        f"• Thời hạn: <b>{dur_text}</b> (<code>{duration}</code>)\n"
        f"• Giá lẻ: <b>{price:,} VNĐ</b>\n"
        f"• Giá Seller VIP: <b>{seller_price:,} VNĐ</b>\n"
        f"• Tồn kho đã nạp: <b>{len(keys)}</b>",
        parse_mode="HTML"
    )

async def lenh_nhap_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    full_text = update.effective_message.text or ""
    parts = full_text.split(None, 2)
    if len(parts) < 3:
        await update.effective_message.reply_text(
            f"{TG_EMOJI['WARNING']} <b>CÚ PHÁP:</b> <code>/nhapkey &lt;Mã_ID_Sản_Phẩm&gt; &lt;Key1, Key2 hoặc mỗi key một dòng&gt;</code>",
            parse_mode="HTML"
        )
        return

    prod_id = parts[1].strip()
    raw_keys = parts[2].strip()
    keys_to_add = [k.strip() for k in re.split(r"[\n,]+", raw_keys) if k.strip()]

    if not keys_to_add:
        await update.effective_message.reply_text(f"{TG_EMOJI['CROSS']} Không tìm thấy key nào để nạp!")
        return

    store_data = tai_du_lieu_cua_hang()
    prod = next((p for p in store_data.get("products", []) if p.get("id") == prod_id), None)

    if not prod:
        await update.effective_message.reply_text(f"{TG_EMOJI['CROSS']} Không tìm thấy sản phẩm có mã <code>{prod_id}</code>!", parse_mode="HTML")
        return

    prod.setdefault("keys", []).extend(keys_to_add)
    prod["stock"] = len(prod["keys"])
    luu_du_lieu_cua_hang(store_data)

    await update.effective_message.reply_text(
        f"{TG_EMOJI['CHECK']} <b>NẠP KEY THÀNH CÔNG!</b>\n"
        f"────────────────────────\n"
        f"• Sản phẩm: <b>{prod.get('name')}</b>\n"
        f"• Đã nạp thêm: <b>+{len(keys_to_add)} key</b>\n"
        f"• Tổng tồn kho hiện tại: <b>{prod['stock']} key</b>",
        parse_mode="HTML"
    )

async def lenh_xoa_san_pham(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if not context.args:
        await update.message.reply_text(f"{TG_EMOJI['WARNING']} Cú pháp: <code>/xoasp &lt;Mã_ID_Sản_Phẩm&gt;</code>", parse_mode="HTML")
        return

    prod_id = context.args[0].strip()
    store_data = tai_du_lieu_cua_hang()
    prods = store_data.get("products", [])

    new_prods = [p for p in prods if p.get("id") != prod_id]
    if len(new_prods) == len(prods):
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Không tìm thấy sản phẩm có ID <code>{prod_id}</code>!", parse_mode="HTML")
        return

    store_data["products"] = new_prods
    luu_du_lieu_cua_hang(store_data)
    await update.message.reply_text(f"🗑️ Đã xoá vĩnh viễn sản phẩm <code>{prod_id}</code> khỏi hệ thống!", parse_mode="HTML")

async def lenh_danh_sach_san_pham(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    store_data = tai_du_lieu_cua_hang()
    prods = store_data.get("products", [])
    if not prods:
        await update.message.reply_text("📦 Kho hàng hiện chưa có sản phẩm nào.")
        return

    msg = f"{TG_EMOJI['SHOPPING']} <b>DANH SÁCH SẢN PHẨM & TỒN KHO (ADMIN):</b>\n────────────────────────\n"
    for p in prods:
        dur = dinh_dang_thoi_gian(p.get("duration", "1d"))
        keys_count = len(p.get("keys", []))
        msg += f"• <b>{p.get('name')}</b> ({dur})\n"
        msg += f"  Mã: <code>{p.get('id')}</code> | Danh mục: <code>{p.get('categoryId')}</code>\n"
        msg += f"  Giá lẻ: <code>{p.get('price', 0):,}đ</code> | Seller: <code>{p.get('sellerPrice', 0):,}đ</code>\n"
        msg += f"  Tồn kho: <b>{p.get('stock', 0)}</b> | Key thực: <b>{keys_count} key</b>\n\n"

    await update.message.reply_text(msg, parse_mode="HTML")

async def lenh_kho_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    store_data = tai_du_lieu_cua_hang()
    prods = store_data.get("products", [])
    if not prods:
        await update.message.reply_text("Kho hàng rỗng.")
        return

    msg = f"{TG_EMOJI['LOCK']} <b>TỔNG QUAN KHO KEY ADMIN:</b>\n────────────────────────\n"
    for p in prods:
        keys = p.get("keys", [])
        dur = dinh_dang_thoi_gian(p.get("duration", "1d"))
        msg += f"📌 <b>{p.get('name')}</b> ({dur}) - Còn: <b>{len(keys)} key</b>\n"
        if keys:
            sample_keys = "\n".join([f"  • <code>{k}</code>" for k in keys[:5]])
            msg += f"{sample_keys}\n"
            if len(keys) > 5:
                msg += f"  <i>...và {len(keys) - 5} key khác</i>\n"
        else:
            msg += "  <i>(Hết key, đang cấp key ảo ngẫu nhiên)</i>\n"
        msg += "\n"

    await update.message.reply_text(msg, parse_mode="HTML")

async def lenh_set_vip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if len(context.args) < 2:
        await update.message.reply_text(f"{TG_EMOJI['WARNING']} Cú pháp: <code>/setvip &lt;Telegram_ID&gt; &lt;seller|customer&gt;</code>", parse_mode="HTML")
        return

    target_uid = str(context.args[0]).strip()
    role = str(context.args[1]).strip().lower()
    if role not in ("seller", "customer"):
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Quyền chỉ được chọn: <code>seller</code> hoặc <code>customer</code>", parse_mode="HTML")
        return

    store_data = tai_du_lieu_cua_hang()
    users = store_data.setdefault("users", {})
    if target_uid not in users:
        users[target_uid] = {
            "balance": 0, "spent": 0, "totalDeposit": 0, "role": role, "inventory": [], "depositHistory": []
        }
    else:
        users[target_uid]["role"] = role

    luu_du_lieu_cua_hang(store_data)
    role_name = "⭐ SELLER VIP" if role == "seller" else "👤 KHÁCH HÀNG"
    await update.message.reply_text(f"{TG_EMOJI['CHECK']} Đã đặt cấp bậc cho ID <code>{target_uid}</code> thành: <b>{role_name}</b>", parse_mode="HTML")

    if target_uid.isdigit():
        gui_tin_nhan_telegram(
            int(target_uid),
            f"{TG_EMOJI['STAR']} <b>CẬP NHẬT CẤP BẬC TÀI KHOẢN!</b>\n"
            f"────────────────────────\n"
            f"Tài khoản của bạn đã được nâng cấp thành: <b>{role_name}</b>!"
        )

async def lenh_cong_tien(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if len(context.args) < 2:
        await update.message.reply_text(f"{TG_EMOJI['WARNING']} Cú pháp: <code>/congtien &lt;Telegram_ID&gt; &lt;Số_tiền&gt;</code>", parse_mode="HTML")
        return

    target_uid = str(context.args[0]).strip()
    try:
        amount = int(re.sub(r"[^\d]", "", context.args[1]))
    except Exception:
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Số tiền không hợp lệ!", parse_mode="HTML")
        return

    store_data = tai_du_lieu_cua_hang()
    users = store_data.setdefault("users", {})
    u = users.setdefault(target_uid, {
        "balance": 0, "spent": 0, "totalDeposit": 0, "role": "customer", "inventory": [], "depositHistory": []
    })
    u["balance"] += amount
    u["totalDeposit"] += amount
    now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    u.setdefault("depositHistory", []).insert(0, {
        "method": "Admin Cộng Tiền",
        "amount": amount,
        "status": "Thành công",
        "time": now_str
    })
    luu_du_lieu_cua_hang(store_data)

    await update.message.reply_text(f"{TG_EMOJI['CHECK']} Đã cộng <b>+{amount:,} VNĐ</b> cho <code>{target_uid}</code>! Số dư mới: <b>{u['balance']:,} VNĐ</b>", parse_mode="HTML")
    if target_uid.isdigit():
        gui_tin_nhan_telegram(int(target_uid), f"{TG_EMOJI['MONEY']} <b>BIẾN ĐỘNG SỐ DƯ:</b>\n• Được cộng: <b>+{amount:,} VNĐ</b>\n• Số dư hiện tại: <b>{u['balance']:,} VNĐ</b>")

async def lenh_tru_tien(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if len(context.args) < 2:
        await update.message.reply_text(f"{TG_EMOJI['WARNING']} Cú pháp: <code>/trutien &lt;Telegram_ID&gt; &lt;Số_tiền&gt;</code>", parse_mode="HTML")
        return

    target_uid = str(context.args[0]).strip()
    try:
        amount = int(re.sub(r"[^\d]", "", context.args[1]))
    except Exception:
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Số tiền không hợp lệ!", parse_mode="HTML")
        return

    store_data = tai_du_lieu_cua_hang()
    users = store_data.setdefault("users", {})
    u = users.setdefault(target_uid, {
        "balance": 0, "spent": 0, "totalDeposit": 0, "role": "customer", "inventory": [], "depositHistory": []
    })
    u["balance"] = max(0, u.get("balance", 0) - amount)
    luu_du_lieu_cua_hang(store_data)

    await update.message.reply_text(f"{TG_EMOJI['CHECK']} Đã trừ <b>-{amount:,} VNĐ</b> của <code>{target_uid}</code>! Số dư mới: <b>{u['balance']:,} VNĐ</b>", parse_mode="HTML")

async def lenh_duyet_nap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if len(context.args) < 2:
        await update.message.reply_text(
            f"{TG_EMOJI['WARNING']} <b>CÚ PHÁP DUYỆT NẠP TIỀN THỦ CÔNG:</b>\n"
            f"<code>/duyetnap &lt;Telegram_ID&gt; &lt;Số_tiền&gt;</code>\n\n"
            f"👉 <b>Ví dụ:</b> <code>/duyetnap 123456789 50000</code>",
            parse_mode="HTML"
        )
        return

    target_uid = str(context.args[0]).strip()
    try:
        amount = int(re.sub(r"[^\d]", "", context.args[1]))
    except Exception:
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Số tiền không hợp lệ!", parse_mode="HTML")
        return

    if amount <= 0:
        await update.message.reply_text(f"{TG_EMOJI['CROSS']} Số tiền phải lớn hơn 0!", parse_mode="HTML")
        return

    store_data = tai_du_lieu_cua_hang()
    users = store_data.setdefault("users", {})
    u = users.setdefault(target_uid, {
        "balance": 0, "spent": 0, "totalDeposit": 0, "role": "customer", "inventory": [], "depositHistory": []
    })
    u["balance"] += amount
    u["totalDeposit"] += amount
    now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    u.setdefault("depositHistory", []).insert(0, {
        "method": "Admin Duyệt Nạp Tay",
        "amount": amount,
        "status": "Thành công",
        "time": now_str
    })

    store_data.setdefault("recentTransactions", []).insert(0, {
        "name": u.get("name", "Khách hàng"),
        "type": "nạp",
        "amount": amount,
        "time": datetime.now().strftime("%H:%M")
    })
    store_data["recentTransactions"] = store_data["recentTransactions"][:15]

    luu_du_lieu_cua_hang(store_data)

    await update.message.reply_text(
        f"{TG_EMOJI['CHECK']} <b>DUYỆT NẠP TIỀN THÀNH CÔNG!</b>\n"
        f"────────────────────────\n"
        f"• Khách: <code>{target_uid}</code>\n"
        f"• Số tiền: <b>+{amount:,} VNĐ</b>\n"
        f"• Số dư mới: <b>{u['balance']:,} VNĐ</b>\n"
        f"• Phương thức: <b>Admin Duyệt Tay</b>\n"
        f"• Thời gian: <code>{now_str}</code>",
        parse_mode="HTML"
    )

    if target_uid.isdigit():
        gui_tin_nhan_telegram(
            int(target_uid),
            f"{TG_EMOJI['FIRE']} <b>NẠP TIỀN THÀNH CÔNG!</b>\n"
            f"────────────────────────\n"
            f"• Số tiền: <b>+{amount:,} VNĐ</b>\n"
            f"• Số dư mới: <b>{u['balance']:,} VNĐ</b>\n"
            f"• Phương thức: Admin duyệt thủ công\n"
            f"• Thời gian: <code>{now_str}</code>\n\n"
            f"Số dư đã được cập nhật tự động!"
        )

async def lenh_thanh_vien(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    store_data = tai_du_lieu_cua_hang()
    users = store_data.get("users", {})
    if not users:
        await update.message.reply_text("Chưa có thành viên nào.")
        return

    msg = f"{TG_EMOJI['USER']} <b>DANH SÁCH THÀNH VIÊN ({len(users)} người):</b>\n────────────────────────\n"
    for uid, u in list(users.items())[-20:]:
        role = "⭐ Seller VIP" if u.get("role") == "seller" else "Khách"
        msg += f"• <b>{u.get('name', 'User')}</b> (<code>{uid}</code>) - {role}\n"
        msg += f"  Số dư: <code>{u.get('balance', 0):,}đ</code> | Đã nạp: <code>{u.get('totalDeposit', 0):,}đ</code>\n"

    await update.message.reply_text(msg, parse_mode="HTML")

async def lenh_them_danh_muc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    raw = " ".join(context.args).strip()
    if not raw or "|" not in raw:
        await update.message.reply_text(f"{TG_EMOJI['WARNING']} Cú pháp: <code>/themdanhmuc Mã_DM | Tên_DM | Icon</code>", parse_mode="HTML")
        return

    parts = [p.strip() for p in raw.split("|")]
    cat_id = parts[0].lower()
    cat_name = parts[1]
    cat_icon = parts[2] if len(parts) > 2 else "fa-gamepad"

    store_data = tai_du_lieu_cua_hang()
    cats = store_data.setdefault("categories", [])
    cats.append({"id": cat_id, "name": cat_name, "icon": cat_icon})
    luu_du_lieu_cua_hang(store_data)

    await update.message.reply_text(f"{TG_EMOJI['CHECK']} Đã thêm danh mục: <b>{cat_name}</b> (<code>{cat_id}</code>)", parse_mode="HTML")

async def lenh_xoa_danh_muc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if not context.args:
        await update.message.reply_text(f"{TG_EMOJI['WARNING']} Cú pháp: <code>/xoadanhmuc &lt;Mã_DM&gt;</code>", parse_mode="HTML")
        return

    cat_id = context.args[0].strip().lower()
    store_data = tai_du_lieu_cua_hang()
    cats = store_data.get("categories", [])
    store_data["categories"] = [c for c in cats if c.get("id") != cat_id]
    luu_du_lieu_cua_hang(store_data)

    await update.message.reply_text(f"🗑️ Đã xoá danh mục <code>{cat_id}</code>!", parse_mode="HTML")

async def lenh_danh_sach_danh_muc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    store_data = tai_du_lieu_cua_hang()
    cats = store_data.get("categories", [])
    prods = store_data.get("products", [])

    if not cats:
        await update.message.reply_text(
            "📁 <b>DANH SÁCH DANH MỤC GAME:</b>\nHiện tại chưa có danh mục nào trên hệ thống.",
            parse_mode="HTML"
        )
        return

    msg = f"📁 <b>DANH SÁCH DANH MỤC TRÊN HỆ THỐNG ({len(cats)} mục):</b>\n────────────────────────\n"
    for i, c in enumerate(cats, 1):
        c_id = c.get("id", "")
        c_name = c.get("name", "")
        c_icon = c.get("icon", "fa-gamepad")
        prod_count = len([p for p in prods if p.get("categoryId") == c_id])
        msg += f"{i}. <b>{c_name}</b> (<code>{c_id}</code>)\n"
        msg += f"   • Icon: <code>{c_icon}</code>\n"
        msg += f"   • Số sản phẩm: <b>{prod_count} gói</b>\n\n"

    await update.message.reply_text(msg, parse_mode="HTML")

async def lenh_cai_dat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return

    if context.args:
        new_notice = " ".join(context.args).strip()
        store_data = tai_du_lieu_cua_hang()
        store_data.setdefault("shopInfo", {})["notice"] = new_notice
        luu_du_lieu_cua_hang(store_data)
        await update.message.reply_text(f"{TG_EMOJI['CHECK']} Đã cập nhật thông báo:\n<i>{new_notice}</i>", parse_mode="HTML")
        return

    store_data = tai_du_lieu_cua_hang()
    shop = store_data.get("shopInfo", {})
    await update.message.reply_text(
        f"⚙️ <b>THÔNG TIN CẤU HÌNH HIỆN TẠI:</b>\n"
        f"────────────────────────\n"
        f"• Tên shop: <b>{shop.get('name')}</b>\n"
        f"• Thông báo: <i>{shop.get('notice')}</i>\n"
        f"• Ngân hàng: <b>MBBank (MB)</b>\n"
        f"• Số TK: <code>{shop.get('bankAccount')}</code>\n"
        f"• Chủ TK: <b>{shop.get('accountName')}</b>",
        parse_mode="HTML"
    )

async def lenh_them_nhac(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    WAITING_MUSIC_USERS.add(user_id)
    await update.message.reply_text("🎵 <b>CÀI ĐẶT NHẠC NỀN MINI APP:</b>\nHãy gửi tệp âm thanh (.mp3, .m4a) vào đây!", parse_mode="HTML")

async def lenh_tao_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    WAITING_PHOTO_USERS.add(user_id)
    await update.message.reply_text("📸 <b>TẠO LINK ẢNH TRỰC TIẾP:</b>\nHãy gửi bức ảnh bạn muốn tạo link vào đây!", parse_mode="HTML")

async def xu_ly_tep_tin_gui_den(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    msg = update.effective_message

    if user_id in WAITING_MUSIC_USERS or (msg.caption and "/addmusic" in msg.caption.lower()):
        audio = msg.audio or msg.voice or msg.document
        if audio and user_id in ADMIN_IDS:
            WAITING_MUSIC_USERS.discard(user_id)
            try:
                tg_file = await context.bot.get_file(audio.file_id)
                allowed_exts = (".mp3", ".m4a", ".wav", ".ogg")
                ext = ".mp3"
                if hasattr(audio, "file_name") and audio.file_name:
                    cand_ext = os.path.splitext(audio.file_name)[1].lower()
                    if cand_ext in allowed_exts:
                        ext = cand_ext
                filename = f"bgm_{int(time.time())}{ext}"
                file_dest = os.path.join(UPLOAD_DIR, filename)
                await tg_file.download_to_drive(file_dest)

                base_url = lay_link_webapp_chuan().rstrip("/")
                music_url = f"{base_url}/uploads/{filename}"

                current_data = tai_du_lieu_cua_hang()
                current_data["musicUrl"] = music_url
                luu_du_lieu_cua_hang(current_data)

                await msg.reply_text(f"🎶 <b>ĐÃ CÀI ĐẶT NHẠC NỀN THÀNH CÔNG!</b>\n• Link: <code>{music_url}</code>", parse_mode="HTML")
                return
            except Exception as e:
                logger.error(f"Lỗi tải nhạc: {e}")
                await msg.reply_text(f"{TG_EMOJI['CROSS']} Lỗi lưu nhạc!", parse_mode="HTML")
                return

    if msg.photo:
        photo = msg.photo[-1]
        caption = (msg.caption or "").strip().lower()

        if user_id in WAITING_PHOTO_USERS or "/taolink" in caption or "tạo link" in caption:
            WAITING_PHOTO_USERS.discard(user_id)
            try:
                tg_file = await context.bot.get_file(photo.file_id)
                allowed_photo_exts = (".jpg", ".jpeg", ".png", ".webp")
                ext = ".jpg"
                if tg_file.file_path:
                    cand_ext = os.path.splitext(tg_file.file_path)[1].lower()
                    if cand_ext in allowed_photo_exts:
                        ext = cand_ext
                filename = f"img_{int(time.time())}_{random.randint(100, 999)}{ext}"
                file_dest = os.path.join(UPLOAD_DIR, filename)
                await tg_file.download_to_drive(file_dest)

                base_url = lay_link_webapp_chuan().rstrip("/")
                image_url = f"{base_url}/uploads/{filename}"

                await msg.reply_text(f"{TG_EMOJI['CHECK']} <b>LINK ẢNH TRỰC TIẾP:</b>\n<code>{image_url}</code>", parse_mode="HTML")
                return
            except Exception as e:
                logger.error(f"Lỗi tải ảnh: {e}")
                await msg.reply_text(f"{TG_EMOJI['CROSS']} Lỗi tạo link ảnh!", parse_mode="HTML")
                return

async def lenh_thong_bao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    full_text = update.effective_message.text or ""
    parts = full_text.split(None, 1)
    content = parts[1].strip() if len(parts) > 1 else ""
    if not content and update.effective_message.reply_to_message:
        content = (update.effective_message.reply_to_message.text or update.effective_message.reply_to_message.caption or "").strip()

    if not content:
        await update.effective_message.reply_text(f"{TG_EMOJI['NOTICE']} Cú pháp: <code>/thongbao [Nội dung cần phát]</code>", parse_mode="HTML")
        return

    store_data = tai_du_lieu_cua_hang()
    target_ids = list(store_data.get("users", {}).keys())

    for aid in ADMIN_IDS:
        if str(aid) not in target_ids:
            target_ids.append(str(aid))

    status_msg = await update.effective_message.reply_text(f"⏳ Đang phát thông báo tới {len(target_ids)} người dùng...")
    success = 0
    now_str = datetime.now().strftime("%H:%M - %d/%m/%Y")

    for uid in target_ids:
        try:
            client_url = lay_link_webapp_chuan()
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"{TG_EMOJI['NOTICE']} <b>THÔNG BÁO TỪ {SHOP_TITLE}</b>\n────────────────────────\n\n{content}\n\n⏰ <code>{now_str}</code>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 MỞ CỬA HÀNG", web_app=WebAppInfo(url=client_url))]])
            )
            success += 1
        except Exception:
            pass

    await status_msg.edit_text(f"{TG_EMOJI['CHECK']} Đã phát thành công tới {success}/{len(target_ids)} người dùng!", parse_mode="HTML")

async def xu_ly_bam_nut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    client_mini_app = lay_link_webapp_chuan()

    if data == "btn_open_shop":
        await query.message.reply_text(
            "🛍️ Bấm nút dưới để mở Mini App:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Mở Cửa Hàng Ngay", web_app=WebAppInfo(url=client_mini_app))
            ]])
        )
    elif data == "btn_my_keys":
        await lenh_kho(update, context)
    elif data == "btn_deposit_info":
        await lenh_nap(update, context)
    elif data == "btn_check_account":
        await lenh_me(update, context)
