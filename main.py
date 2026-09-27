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

# 1. Đọc biến môi trường từ Render.com
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    print("⚠️ CẢNH BÁO: Chưa cấu hình GROQ_API_KEY hoặc TELEGRAM_TOKEN trên Render!")

# Khởi tạo Groq Client
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Trạng thái cuộc hội thoại (Conversation States)
WAITING_LOGIN_INFO = 1
WAITING_CAPTCHA_INPUT = 2

# URL API Web MB Bank (Official)
MB_CAPTCHA_URL = "https://online.mbbank.com.vn/api/retail-web-internetbankingms/v1.0/client/get-captcha"
MB_LOGIN_URL = "https://online.mbbank.com.vn/api/retail-web-internetbankingms/v1.0/client/login"

# Header mô phỏng trình duyệt Chrome khi gửi request lên MB Bank
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
            model="openai/gpt-oss-20b", # Hoặc llama-3.2-11b-vision-preview
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Đây là ảnh captcha. Hãy đọc chính xác các ký tự/chữ số trong ảnh và chỉ trả về duy nhất chuỗi ký tự đó, không viết thêm từ ngữ nào khác."
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
        print(f"[GROQ ERROR] Lỗi khi gọi Groq API: {e}")
        return ""


# --- HÀM TẢI CAPTCHA THỰC TẾ TỪ WEB MB BANK ---
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
            print(f"[MB CAPTCHA ERROR] Lỗi tải Captcha: {e}")
    return None


# --- HÀM GỬI YÊU CẦU ĐĂNG NHẬP LÊN MB BANK ---
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
                msg = res_data.get("message", "Đăng nhập thất bại hoặc sai Captcha/Mật khẩu.")
                return False, msg
        except Exception as e:
            return False, f"Lỗi kết nối MB Bank: {e}"


# --- 1. LỆNH /start & MENU CHÍNH ---
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


# --- 2. MENU "QUẢN LÝ NGÂN HÀNG" ---
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


# --- 3. BẤM "MB BANK" -> YÊU CẦU NHẬP USER|PASS ---
async def ask_mb_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📝 <b>NHẬP THÔNG TIN ĐĂNG NHẬP MB BANK (online.mbbank.com.vn)</b>\n\n"
        "Vui lòng gửi thông tin theo định dạng:\n"
        "<code>Tên_đăng_nhập|Mật_khẩu</code>\n\n"
        "<i>Ví dụ: 0987654321|MatKhau123</i>",
        parse_mode="HTML"
    )
    return WAITING_LOGIN_INFO


# --- 4. XỬ LÝ NHẬP USER|PASS & TẢI CAPTCHA MB BANK ---
async def process_login_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "|" not in text:
        await update.message.reply_text(
            "❌ <b>Sai định dạng!</b>\nVui lòng nhập đúng dạng <code>Tài_khoản|Mật_khẩu</code>:",
            parse_mode="HTML"
        )
        return WAITING_LOGIN_INFO

    username, password = text.split("|", 1)
    context.user_data['mb_user'] = username.strip()
    context.user_data['mb_pass'] = password.strip()

    await update.message.reply_text("🔄 Đã nhận thông tin. Đang kết nối MB Bank & tải Captcha...")

    # 1. Tải Captcha thực tế từ MB Bank
    captcha_bytes = await fetch_mb_captcha()
    
    if not captcha_bytes:
        await update.message.reply_text("❌ Không thể lấy Captcha từ MB Bank vào lúc này. Vui lòng thử lại sau bằng lệnh /start.")
        return ConversationHandler.END

    context.user_data['captcha_bytes'] = captcha_bytes

    # 2. Gửi cho Groq AI giải
    await update.message.reply_text("🤖 Đang dùng Groq AI để giải Captcha...")
    ai_result = solve_captcha_with_groq(captcha_bytes)
    print(f"[AI RESULT] Groq dự đoán Captcha: '{ai_result}'")

    # 3. Kiểm tra với MB Bank
    is_success = False
    error_msg = ""
    if ai_result:
        is_success, error_msg = await verify_mb_login(
            context.user_data['mb_user'], 
            context.user_data['mb_pass'], 
            ai_result
        )

    # NẾU THÀNH CÔNG
    if is_success:
        await update.message.reply_text(
            f"✅ <b>Đăng nhập MB Bank thành công!</b>\n"
            f"🔑 Mã Captcha AI giải: <code>{ai_result}</code>\n"
            f"🚀 Đã kích hoạt hệ thống tự động theo dõi biến động số dư.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    # NẾU AI GIẢI SAI HOẶC THẤT BẠI -> GỬI ẢNH QUA TELEGRAM
    await update.message.reply_text(
        f"⚠️ Groq AI không giải chính xác Captcha ({error_msg}).\n"
        "📩 Vui lòng nhìn ảnh bên dưới và tự gõ nhập mã giúp mình:"
    )

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=BytesIO(captcha_bytes),
        caption="👇 Gõ lại các ký tự trong ảnh trên để đăng nhập:"
    )

    return WAITING_CAPTCHA_INPUT


# --- 5. BẮT CAPTCHA NGƯỜI DÙNG NHẬP TAY ---
async def process_manual_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_captcha = update.message.text.strip()

    await update.message.reply_text(
        f"📥 Đã nhận Captcha: <code>{user_captcha}</code>\n⏳ Đang gửi yêu cầu đăng nhập lên MB Bank...",
        parse_mode="HTML"
    )

    is_success, error_msg = await verify_mb_login(
        context.user_data.get('mb_user'),
        context.user_data.get('mb_pass'),
        user_captcha
    )

    if is_success:
        await update.message.reply_text(
            "🎉 <b>Đăng nhập thành công!</b>\n"
            "📊 Hệ thống đã lưu tài khoản MB Bank và sẵn sàng nhận thông báo biến động số dư.",
            parse_mode="HTML"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"❌ <b>Đăng nhập thất bại:</b> {error_msg}\n"
            "Nhấn /start để thực hiện lại từ đầu."
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Đã hủy thao tác.")
    return ConversationHandler.END


# --- CHẠY ỨNG DỤNG ---
if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        raise ValueError("Chưa thiết lập biến môi trường TELEGRAM_TOKEN!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Luồng đăng nhập MB Bank
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

    # Đăng ký Handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_to_main$"))
    app.add_handler(CallbackQueryHandler(show_bank_menu, pattern="^menu_banks$"))
    app.add_handler(login_conv)

    print("Bot đang hoạt động...")
    app.run_polling()
