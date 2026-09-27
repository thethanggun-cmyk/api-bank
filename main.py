import os
import uuid
import base64
from io import BytesIO
import httpx
from groq import Groq

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# 1. Đọc cấu hình từ Render
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Các trạng thái luồng hội thoại
WAITING_LOGIN_INFO = 1
WAITING_CAPTCHA_INPUT = 2

# API MB Bank Web
MB_CAPTCHA_URL = "https://online.mbbank.com.vn/api/retail-web-internetbankingms/v1.0/client/get-captcha"
MB_LOGIN_URL = "https://online.mbbank.com.vn/api/retail-web-internetbankingms/v1.0/client/login"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://online.mbbank.com.vn",
    "Referer": "https://online.mbbank.com.vn/pl/login",
}


# --- HÀM GIẢI CAPTCHA BẰNG GROQ AI ---
def solve_captcha_with_groq(image_bytes: bytes) -> str:
    if not client:
        return ""
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Hãy đọc chính xác các ký tự trong ảnh captcha này. Chỉ trả về duy nhất chuỗi ký tự đó, không thêm bất kỳ từ ngữ nào khác."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=20
        )
        
        captcha_text = response.choices[0].message.content.strip()
        return "".join(captcha_text.split())
    except Exception as e:
        print(f"[GROQ ERROR] Lỗi API: {e}")
        return ""


# --- HÀM TẢI CAPTCHA MB BANK ---
async def fetch_mb_captcha() -> bytes:
    headers = HEADERS.copy()
    headers["X-Request-Id"] = str(uuid.uuid4())
    payload = {
        "refNo": str(uuid.uuid4()),
        "deviceIdCommon": "g2y1k2p3-mbb-web-deviceId-default"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        try:
            res = await http_client.post(MB_CAPTCHA_URL, json=payload, headers=headers)
            data = res.json()
            if data.get("status") == "00" and "imageString" in data:
                return base64.b64decode(data["imageString"])
        except Exception as e:
            print(f"[MB CAPTCHA ERROR]: {e}")
    return None


# --- HÀM GỬI LOGIN MB BANK ---
async def verify_mb_login(username, password, captcha_code) -> tuple[bool, str]:
    headers = HEADERS.copy()
    headers["X-Request-Id"] = str(uuid.uuid4())
    payload = {
        "userId": username,
        "password": password,
        "captcha": captcha_code,
        "refNo": str(uuid.uuid4()),
        "deviceIdCommon": "g2y1k2p3-mbb-web-deviceId-default"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        try:
            res = await http_client.post(MB_LOGIN_URL, json=payload, headers=headers)
            res_data = res.json()
            if res_data.get("status") == "00":
                return True, "Đăng nhập thành công!"
            else:
                msg = res_data.get("message", "Đăng nhập thất bại (Sai captcha/mật khẩu).")
                return False, msg
        except Exception as e:
            return False, f"Lỗi kết nối MB Bank: {e}"


# --- 1. LỆNH /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = user.full_name

    text = (
        f"🤖 <b>HỆ THỐNG THUÊ API BANK & THÔNG BÁO BIẾN ĐỘNG SỐ DƯ</b>\n"
        f"<b>________________________________________</b>\n\n"
        f"👋 <b>Xin chào, {full_name}!</b>\n\n"
        f"💳 <b>Số dư ví:</b> 0 đ\n"
        f"📦 <b>Gói cước:</b> 🎁 Dùng Thử 1 Ngày\n"
        f"⏳ <b>Hạn dùng:</b> 28/09/2026 21:45\n"
        f"🔑 <b>API Key:</b> bk_live_6826...\n\n"
        f"Hệ thống hỗ trợ quét tự động biến động số dư ngân hàng và USDT, "
        f"bắn thông báo về Telegram & Webhook về website bán hàng ngay lập tức!"
    )

    keyboard = [
        [
            InlineKeyboardButton("👤 Tài khoản", callback_data="account"),
            InlineKeyboardButton("💳 Nạp tiền", callback_data="deposit"),
        ],
        [
            InlineKeyboardButton("📦 Gói cước / Thuê bot", callback_data="plans"),
            InlineKeyboardButton("🏦 Quản lý Ngân hàng", callback_data="menu_banks"),
        ],
        [
            InlineKeyboardButton("⚡ Webhook & API", callback_data="webhook"),
            InlineKeyboardButton("🔔 Nhận thông báo", callback_data="notifications"),
        ],
        [
            InlineKeyboardButton("📊 Lịch sử giao dịch", callback_data="history"),
            InlineKeyboardButton("📖 Hướng dẫn", callback_data="docs"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


# --- 2. MENU QUẢN LÝ NGÂN HÀNG ---
async def show_bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🏦 MB BANK", callback_data="select_mbbank")],
        [InlineKeyboardButton("🔙 Quay lại Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🏦 <b>QUẢN LÝ NGÂN HÀNG</b>\n\nVui lòng chọn ngân hàng bạn muốn kết nối:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


# --- 3. YÊU CẦU NHẬP USER|PASS ---
async def ask_mb_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📝 <b>NHẬP THÔNG TIN ĐĂNG NHẬP MB BANK</b>\n\n"
        "Vui lòng nhập đúng cú pháp:\n"
        "<code>Tên_đăng_nhập|Mật_khẩu</code>\n\n"
        "<i>Ví dụ: 0987654321|MatKhau123</i>",
        parse_mode="HTML"
    )
    return WAITING_LOGIN_INFO


# --- 4. XỬ LÝ NHẬP TÀI KHOẢN, TẢI CAPTCHA VÀ GỬI CẢ ẢNH + ĐÁP ÁN AI CHO BẠN ---
async def process_login_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    if "|" not in text:
        await update.message.reply_text(
            "❌ <b>Sai cú pháp!</b> Vui lòng nhập dạng <code>Tài_khoản|Mật_khẩu</code>:",
            parse_mode="HTML"
        )
        return WAITING_LOGIN_INFO

    username, password = text.split("|", 1)
    context.user_data['mb_user'] = username.strip()
    context.user_data['mb_pass'] = password.strip()

    await update.message.reply_text("🔄 Đang tải Captcha từ MB Bank...")

    # Tải Captcha thực tế từ MB Bank
    captcha_bytes = await fetch_mb_captcha()
    
    if not captcha_bytes:
        await update.message.reply_text("❌ Không lấy được Captcha từ MB Bank. Vui lòng gõ /start để thử lại.")
        return ConversationHandler.END

    # Cho Groq AI đọc Captcha
    ai_result = solve_captcha_with_groq(captcha_bytes)

    # 🛑 GỬI NGAY ẢNH CAPTCHA CÙNG ĐÁP ÁN AI ĐÃ ĐỌC QUA TELEGRAM CHO BẠN XEM
    caption_text = f"📸 <b>Ảnh Captcha từ MB Bank</b>\n🤖 AI đọc được: <code>{ai_result if ai_result else 'Không đọc được'}</code>\n\n⏳ <i>Đang thử gửi lên MB Bank...</i>"
    
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=BytesIO(captcha_bytes),
        caption=caption_text,
        parse_mode="HTML"
    )

    # Thử gửi kết quả AI lên MB Bank
    is_success = False
    error_msg = ""
    if ai_result:
        is_success, error_msg = await verify_mb_login(
            context.user_data['mb_user'], 
            context.user_data['mb_pass'], 
            ai_result
        )

    # Nếu AI đoán ĐÚNG -> Thành công luôn
    if is_success:
        await update.message.reply_text(
            "🎉 <b>Đăng nhập MB Bank thành công!</b>\n"
            "🚀 Đã kích hoạt hệ thống tự động quét biến động số dư.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    # Nếu AI đoán SAI -> Báo lỗi và chờ bạn nhập lại mã đúng
    await update.message.reply_text(
        f"❌ AI đoán mã '<code>{ai_result}</code>' không đúng ({error_msg}).\n\n"
        "👉 <b>Vui lòng nhìn bức ảnh Captcha ở trên và gõ lại mã chuẩn vào đây giúp mình:</b>",
        parse_mode="HTML"
    )

    return WAITING_CAPTCHA_INPUT


# --- 5. XỬ LÝ KHI BẠN TỰ GÕ LẠI CAPTCHA CHUẨN ---
async def process_manual_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_captcha = update.message.text.strip()

    await update.message.reply_text(
        f"📥 Đã nhận mã bạn nhập: <code>{user_captcha}</code>\n⏳ Đang gửi lên MB Bank...",
        parse_mode="HTML"
    )

    is_success, error_msg = await verify_mb_login(
        context.user_data.get('mb_user'),
        context.user_data.get('mb_pass'),
        user_captcha
    )

    if is_success:
        await update.message.reply_text(
            "🎉 <b>Đăng nhập MB Bank thành công!</b>\n"
            "📊 Hệ thống đã bắt đầu lưu phiên làm việc và theo dõi biến động.",
            parse_mode="HTML"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"❌ <b>Đăng nhập thất bại:</b> {error_msg}\n"
            "Gõ /start để thử lại từ đầu."
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đã hủy thao tác.")
    return ConversationHandler.END


# --- MAIN ---
if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        raise ValueError("Chưa thiết lập TELEGRAM_TOKEN!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    login_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_mb_credentials, pattern="^select_mbbank$")],
        states={
            WAITING_LOGIN_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_login_info)
            ],
            WAITING_CAPTCHA_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_manual_captcha)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(show_bank_menu, pattern="^menu_banks$"))
    app.add_handler(login_conv)

    print("Bot đang chạy...")
    app.run_polling()
