import os
import asyncio
import yt_dlp

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest


BOT_TOKEN = "8917640567:AAHRs_bBIrtCHeaK8ydVFL88r8Y3yYJQe5M"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 أرسل رابط أغنية من يوتيوب."
    )


async def download_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("❌ الرابط غير صحيح")
        return

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    os.makedirs("downloads", exist_ok=True)

    options = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {
                "key": "EmbedThumbnail"
            },
            {
                "key": "FFmpegMetadata"
            }
        ]
    }

    try:
        loop = asyncio.get_running_loop()

        def get_audio():
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = filename.rsplit(".", 1)[0] + ".mp3"
                return filename, info

        filename, info = await loop.run_in_executor(None, get_audio)

        await msg.edit_text("📤 جاري رفع الأغنية...")

        title = info.get("title", "Audio")
        artist = info.get("artist") or info.get("uploader", "Unknown")

        with open(filename, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                title=title,
                performer=artist,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=120
            )

        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ:\n{e}")


if __name__ == "__main__":

    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=120,
        write_timeout=120,
        pool_timeout=60
    )

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(request)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, download_song)
    )

    print("Bot is running...")
    app.run_polling()
