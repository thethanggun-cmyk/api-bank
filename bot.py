import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SHOP_NAME = " Name - Store Hack"
os.environ["SHOP_NAME"] = SHOP_NAME

import logging
import threading
from http.server import ThreadingHTTPServer
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from telegram import MenuButtonWebApp, WebAppInfo
from config import BOT_TOKEN, ADMIN_IDS, WEBAPP_URL
from server_handler import SecurityHTTPHandler, lay_link_webapp_chuan
from bot_handlers import (
    lenh_start, lenh_kho, lenh_me, lenh_nap, lenh_ds, lenh_top,
    lenh_admin, lenh_them_san_pham, lenh_nhap_key, lenh_xoa_san_pham, lenh_danh_sach_san_pham, lenh_kho_key,
    lenh_set_vip, lenh_cong_tien, lenh_tru_tien, lenh_duyet_nap, lenh_thanh_vien, lenh_them_danh_muc,
    lenh_xoa_danh_muc, lenh_danh_sach_danh_muc, lenh_cai_dat, lenh_them_nhac, lenh_tao_link,
    lenh_thong_bao, xu_ly_tep_tin_gui_den, xu_ly_bam_nut
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("StoreBot")

def chay_may_chu_web_ngam():
    port = int(os.environ.get("PORT", 10000))
    server = ThreadingHTTPServer(("0.0.0.0", port), SecurityHTTPHandler)
    logger.info(f"Web server {SHOP_NAME} Mini App đã mở trên cổng {port}!")
    server.serve_forever()

async def khoi_tao_sau(application):
    try:
        clean_url = lay_link_webapp_chuan()
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🚀 Mở Cửa Hàng", web_app=WebAppInfo(url=clean_url))
        )
        logger.info(f"Đã thiết lập Telegram Menu Button tự động: {clean_url}")
    except Exception as e:
        logger.warning(f"Không thể thiết lập Telegram Menu Button: {e}")

def chay_chinh():
    print("==================================================")
    print(f"{SHOP_NAME.upper()}")
    print(f"Admin IDs: {ADMIN_IDS}")
    print("==================================================")

    web_thread = threading.Thread(target=chay_may_chu_web_ngam, daemon=True)
    web_thread.start()

    if not BOT_TOKEN:
        logger.error("Chưa thiết lập BOT_TOKEN trong biến môi trường!")
        return

    if not WEBAPP_URL:
        logger.error("Chưa thiết lập WEBAPP_URL (hoặc RENDER_EXTERNAL_URL) trong biến môi trường!")
        return

    if not ADMIN_IDS:
        logger.warning("Chưa thiết lập ADMIN_IDS, các lệnh quản trị sẽ không dùng được!")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(khoi_tao_sau).build()

    app.add_handler(CommandHandler("start", lenh_start))
    app.add_handler(CommandHandler("kho", lenh_kho))
    app.add_handler(CommandHandler("me", lenh_me))
    app.add_handler(CommandHandler("nap", lenh_nap))
    app.add_handler(CommandHandler("ds", lenh_ds))
    app.add_handler(CommandHandler("top", lenh_top))

    app.add_handler(CommandHandler("admin", lenh_admin))
    app.add_handler(CommandHandler("themsp", lenh_them_san_pham))
    app.add_handler(CommandHandler("nhapkey", lenh_nhap_key))
    app.add_handler(CommandHandler("xoasp", lenh_xoa_san_pham))
    app.add_handler(CommandHandler("dssp", lenh_danh_sach_san_pham))
    app.add_handler(CommandHandler("khokey", lenh_kho_key))
    app.add_handler(CommandHandler("setvip", lenh_set_vip))
    app.add_handler(CommandHandler("congtien", lenh_cong_tien))
    app.add_handler(CommandHandler("trutien", lenh_tru_tien))
    app.add_handler(CommandHandler("duyetnap", lenh_duyet_nap))
    app.add_handler(CommandHandler("thanhvien", lenh_thanh_vien))
    app.add_handler(CommandHandler("themdanhmuc", lenh_them_danh_muc))
    app.add_handler(CommandHandler("xoadanhmuc", lenh_xoa_danh_muc))
    app.add_handler(CommandHandler("dsdanhmuc", lenh_danh_sach_danh_muc))
    app.add_handler(CommandHandler("caidat", lenh_cai_dat))
    app.add_handler(CommandHandler("addmusic", lenh_them_nhac))
    app.add_handler(CommandHandler("taolink", lenh_tao_link))
    app.add_handler(CommandHandler("thongbao", lenh_thong_bao))

    media_filter = filters.PHOTO | filters.AUDIO | filters.VOICE | filters.Document.ALL
    app.add_handler(MessageHandler(media_filter, xu_ly_tep_tin_gui_den))
    app.add_handler(CallbackQueryHandler(xu_ly_bam_nut))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    chay_chinh()