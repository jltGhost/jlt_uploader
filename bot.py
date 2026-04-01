import logging
import os
import uuid
import asyncio
from pathlib import Path
import aiohttp
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO)

async def download_direct(url):
    filepath = DOWNLOAD_DIR / f"{uuid.uuid4().hex}.mp4"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                async for chunk in resp.content.iter_chunked(65536):
                    f.write(chunk)
    return str(filepath)

def download_ytdlp(url):
    out = DOWNLOAD_DIR / f"{uuid.uuid4().hex}.mp4"
    opts = {
        "outtmpl": str(out),
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a video URL!\n"
        "Supports YouTube, TikTok, Twitter, Instagram, direct .mp4 links and more."
    )

async def handle_url(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text("⏳ Starting download...")
    filepath = None

    try:
        try:
            await msg.edit_text("⏳ Downloading with yt-dlp...")
            filepath = download_ytdlp(url)
        except Exception:
            await msg.edit_text("⏳ Trying direct download...")
            filepath = await download_direct(url)

        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > 50:
            await msg.edit_text(f"❌ File too large ({size_mb:.1f} MB). Max is 50 MB.")
            return

        await msg.edit_text(f"📤 Uploading ({size_mb:.1f} MB)...")
        with open(filepath, "rb") as f:
            await update.message.reply_video(
                video=f,
                supports_streaming=True,
                read_timeout=180,
                write_timeout=180,
            )
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Failed: {e}")
    finally:
        if filepath:
            try:
                os.remove(filepath)
            except:
                pass

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    print("✅ Bot is running!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

---
