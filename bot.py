import asyncio
import logging
import yfinance as yf
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = '7751395968:AAFe1pThvDb8EH7mubKRirj5koWMR5X2uns'
CHAT_ID = '6652798946'
kapitalas = 300
norimas_pelnas = 10
intervalas_rinkos = 15  # minutėmis

logging.basicConfig(level=logging.INFO)

app = Application.builder().token(TOKEN).build()

def gauti_rsi(df, laikotarpis=14):
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=laikotarpis - 1, adjust=False).mean()
    ema_down = down.ewm(com=laikotarpis - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

async def siusti_signala():
    df = yf.download(tickers='ETH-USD', period='1d', interval=f'{intervalas_rinkos}m', progress=False)
    kaina = float(df['Close'].iloc[-1])
    rsi = float(gauti_rsi(df).iloc[-1])

    if rsi < 30:
        signalas = f'📉 LAUKTI!\nETH: {kaina:.2f} USD\nRSI: {rsi:.2f}\n🟢 Siunčiama automatiškai.'
    elif rsi > 70:
        signalas = f'📈 LAUKTI!\nETH: {kaina:.2f} USD\nRSI: {rsi:.2f}\n🔴 Siunčiama automatiškai.'
    else:
        signalas = f'📊 NEUTRALU\nETH: {kaina:.2f} USD\nRSI: {rsi:.2f}\n⚪ Siunčiama automatiškai.'

    await app.bot.send_message(chat_id=CHAT_ID, text=signalas)

async def periodinis_tikrinimas():
    while True:
        await siusti_signala()
        await asyncio.sleep(intervalas_rinkos * 60)

def sukurti_mygtukus():
    keyboard = [
        [InlineKeyboardButton("📡 Signalas", callback_data='signalas')],
        [InlineKeyboardButton("📊 Statistika", callback_data='statistika')],
        [InlineKeyboardButton("📕 Log", callback_data='log')],
        [InlineKeyboardButton("⛔ Stop", callback_data='stop')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Botas paleistas ir veikia.\n\nPasirinkite veiksmą:", reply_markup=sukurti_mygtukus())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'signalas':
        await siusti_signala()
    elif query.data == 'statistika':
        await query.edit_message_text(text="📊 Statistika dar ruošiama.")
    elif query.data == 'log':
        await query.edit_message_text(text="📕 Log dar ruošiamas.")
    elif query.data == 'stop':
        await query.edit_message_text(text="⛔ Botas sustabdytas.")
        await app.stop()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback_handler))

async def paleisti():
    await app.initialize()
    await app.start()
    asyncio.create_task(periodinis_tikrinimas())
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(paleisti())
