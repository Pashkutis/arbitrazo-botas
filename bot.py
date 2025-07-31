import os
import logging
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Pagrindinis loggeris
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Globalūs kintamieji
kapitalas = 300
pelnas = 20
intervalas = 15
paskutinis_signalas = {}

# Komandos
async def start(update, context):
    await update.message.reply_text("Botas paleistas!")

async def kapitalas_cmd(update, context):
    await update.message.reply_text(f"Kapitalas: {kapitalas} USDT")

async def pelnas_cmd(update, context):
    await update.message.reply_text(f"Tikslinis pelnas per ciklą: {pelnas} USDT")

async def signal(update, context):
    await update.message.reply_text("Testinis signalas veikia!")

async def statistika(update, context):
    await update.message.reply_text("Statistika dar renkama...")

async def stop(update, context):
    await update.message.reply_text("Botas sustabdytas.")

async def intervalas_cmd(update, context):
    await update.message.reply_text(f"Signalų tikrinimo intervalas: {intervalas} min.")

async def log(update, context):
    await update.message.reply_text("Log dar neįgyvendintas.")

# Paleidimo funkcija
async def paleisti():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kapitalas", kapitalas_cmd))
    app.add_handler(CommandHandler("pelnas", pelnas_cmd))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("intervalas", intervalas_cmd))
    app.add_handler(CommandHandler("log", log))

    print("Botas paleistas ir laukia komandų...")
    await app.run_polling()

# Teisingas paleidimas
if __name__ == "__main__":
    asyncio.run(paleisti())
