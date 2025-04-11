
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

SPOT_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"]

COINGECKO_MAPPING = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "XRPUSDT": "ripple",
    "BNBUSDT": "binancecoin"
}

# --- Ціни з Binance ---
def get_binance_signal(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        response = requests.get(url).json()
        price = float(response['lastPrice'])
        change = float(response['priceChangePercent'])
        direction = "📈 Купити" if change > 0 else "📉 Продати"
        return f"📊 Binance {symbol}\nЦіна: {price:.2f} USDT\nЗміна за 24h: {change:.2f}% → {direction}"
    except Exception as e:
        return f"❌ Помилка Binance: {e}"

# --- Ціни з CoinGecko ---
def get_coingecko_signal(symbol):
    coin_id = COINGECKO_MAPPING.get(symbol)
    if not coin_id:
        return f"❌ Не знайдено монету {symbol} на CoinGecko."

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url).json()
        price = response[coin_id]['usd']
        change = response[coin_id]['usd_24hr_change']
        direction = "📈 Купити" if change > 0 else "📉 Продати"
        return f"🟢 CoinGecko {symbol}\nЦіна: {price:.2f} USD\nЗміна: {change:.2f}% → {direction}"
    except Exception as e:
        return f"❌ Помилка CoinGecko: {e}"

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(symbol[:-4], callback_data=symbol)] for symbol in SPOT_PAIRS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("💰 Обери монету для сигналу:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("💰 Обери монету для сигналу:", reply_markup=reply_markup)

# --- Обробка монети ---
async def coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data

    keyboard = [
        [InlineKeyboardButton("📊 Binance", callback_data=f"binance|{symbol}")],
        [InlineKeyboardButton("🟢 CoinGecko", callback_data=f"coingecko|{symbol}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🔍 Обрана монета: {symbol}\nОбери джерело:", reply_markup=reply_markup)

# --- Відповідь на джерело ---
async def exchange_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    source, symbol = query.data.split("|")

    if source == "coingecko":
        text = get_coingecko_signal(symbol)
    elif source == "binance":
        text = get_binance_signal(symbol)
    else:
        text = "❌ Невідоме джерело"

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=symbol)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

# --- Повернення до меню ---
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(query, context)

# --- Запуск бота ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(exchange_selected, pattern=r"^(binance|coingecko)\|"))
    app.add_handler(CallbackQueryHandler(coin_selected, pattern=r"^[A-Z]+USDT$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern=r"^back_to_menu$"))

    print("✅ Бот запущено")
    app.run_polling()
