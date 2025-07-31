# Importuoti reikalingas bibliotekas
import yfinance as yf
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
from pytz import timezone
import nest_asyncio

nest_asyncio.apply()

# Tavo duomenys
TOKEN = '7751395968:AAFe1pThvDb8EH7mubKRirj5koWMR5X2uns'
CHAT_ID = '6652798946'

# Pradiniai kintamieji
kapitalas = 300
norimas_pelnas = 10
intervalas_rinkos = 15
pirkimo_kaina = None
stop_signalas = False
log_list = []

# Komandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Botas paleistas ir veikia.")

async def kapitalas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global kapitalas
    try:
        kapitalas = float(context.args[0])
        await update.message.reply_text(f"💵 Kapitalas nustatytas: {kapitalas} USDT")
    except:
        await update.message.reply_text("❌ Naudok: /kapitalas 300")

async def pelnas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global norimas_pelnas, pirkimo_kaina
    try:
        if len(context.args) == 2:
            norimas_pelnas = float(context.args[0])
            pirkimo_kaina = float(context.args[1])
        else:
            norimas_pelnas = float(context.args[0])
        
        if pirkimo_kaina:
            reikalinga_kaina = pirkimo_kaina + (norimas_pelnas / (kapitalas / pirkimo_kaina))
            reikalinga_kaina = round(reikalinga_kaina, 2)
            await update.message.reply_text(
                f"📌 Norimas pelnas: {norimas_pelnas} USDT\n"
                f"📈 Pirkimo kaina: {pirkimo_kaina}\n"
                f"🏁 Reikia parduoti @: {reikalinga_kaina} USDT"
            )
        else:
            await update.message.reply_text(f"💰 Norimas pelnas: {norimas_pelnas} USDT")
    except:
        await update.message.reply_text("❌ Naudok: /pelnas 10 arba /pelnas 10 3770")

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stop_signalas
    stop_signalas = True
    await update.message.reply_text("🛑 Botas sustabdytas. Nebesiunčia signalų.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await siusti_signal(False)

async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pirkimo_kaina
    df = yf.download(tickers='ETH-USD', period='1d', interval=f'{intervalas_rinkos}m')
    price = float(df['Close'].iloc[-1])
    rsi = skaiciuoti_rsi(df)
    now = datetime.now(timezone('Europe/Vilnius')).strftime("%Y-%m-%d %H:%M:%S")

    if pirkimo_kaina:
        reikalinga_kaina = pirkimo_kaina + (norimas_pelnas / (kapitalas / pirkimo_kaina))
        reikalinga_kaina = round(reikalinga_kaina, 2)
    else:
        reikalinga_kaina = "-"

    await update.message.reply_text(
        f"🔹 Paskutinis signalas:\n"
        f"📅 Laikas: {now}\n"
        f"📈 ETH kaina: {price} USD\n"
        f"🔢 RSI: {rsi:.2f}\n"
        f"📊 Pirkimo kaina: {pirkimo_kaina if pirkimo_kaina else '-'}\n"
        f"🌟 Reikia parduoti @: {reikalinga_kaina} USDT"
    )

async def intervalas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global intervalas_rinkos
    try:
        arg = context.args[0].lower().replace("m", "")
        intervalas_rinkos = int(arg)
        await update.message.reply_text(f"⏱️ Tikrinimo intervalas nustatytas: {intervalas_rinkos} min.")
    except:
        await update.message.reply_text("❌ Naudok: /intervalas 10 arba /intervalas 5m")

async def log_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not log_list:
        await update.message.reply_text("📭 Dar nėra jokių signalų žurnale.")
        return

    zinute = "📜 Paskutiniai signalai:\n\n"
    for row in log_list[-5:][::-1]:
        zinute += f"{row}\n\n"

    await update.message.reply_text(zinute)

def skaiciuoti_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

async def siusti_signal(automatinis):
    global pirkimo_kaina, stop_signalas
    if stop_signalas:
        return

    df = yf.download(tickers='ETH-USD', period='1d', interval=f'{intervalas_rinkos}m')
    price = float(df['Close'].iloc[-1])
    rsi_value = skaiciuoti_rsi(df)
    now = datetime.now(timezone('Europe/Vilnius')).strftime("%Y-%m-%d %H:%M:%S")

    if rsi_value < 30:
        pirkimo_kaina = price
        reikalinga = pirkimo_kaina + (norimas_pelnas / (kapitalas / pirkimo_kaina))
        reikalinga = round(reikalinga, 2)
        zinute = f"✅ PIRKTI!\n📈 ETH: {price:.2f} USD\n🔢 RSI: {rsi_value:.2f}\n🌟 Pardavimo kaina: {reikalinga} USDT"
    elif rsi_value > 70:
        zinute = f"❌ PARDUOTI!\n📈 ETH: {price:.2f} USD\n🔢 RSI: {rsi_value:.2f}"
        pirkimo_kaina = None
    else:
        zinute = f"🚫 LAUKTI!\n📈 ETH: {price:.2f} USD\n🔢 RSI: {rsi_value:.2f}"

    if automatinis:
        zinute += "\n🤖 Siunčiama automatiškai."

    log_list.append(f"🕒 {now}\n{zinute}")
    await Bot(token=TOKEN).send_message(chat_id=CHAT_ID, text=zinute)

async def periodinis_tikrinimas():
    while not stop_signalas:
        await siusti_signal(True)
        await asyncio.sleep(intervalas_rinkos * 60)

async def paleisti():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kapitalas", kapitalas_cmd))
    app.add_handler(CommandHandler("pelnas", pelnas_cmd))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("intervalas", intervalas_cmd))
    app.add_handler(CommandHandler("log", log_cmd))
    asyncio.create_task(periodinis_tikrinimas())
    await app.run_polling()

await paleisti()
