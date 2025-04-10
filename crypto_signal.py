from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

BOT_TOKEN = "7750637434:AAFg5mKGJCCtUcrAV4vIWyKPBOykN1RdBp8"  # Замініть на свій токен

SPOT_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"]

# Отримуємо сигнали з Binance
def get_binance_signal(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        response = requests.get(url).json()
        price = float(response['lastPrice'])
        change = float(response['priceChangePercent'])
        direction = "📈 Купити" if change > 0 else "📉 Продати"
        return f"🔵 Binance {symbol}\nЦіна: {price:.2f}\nЗміна: {change:.2f}% → {direction}"
    except Exception as e:
        return f"❌ Помилка з Binance: {e}"

# Отримуємо сигнали з Bybit
def get_bybit_signal(symbol):
    url = "https://api.bybit.com/v2/public/tickers"
    try:
        response = requests.get(url).json()
        for data in response["result"]:
            if data['symbol'] == symbol:
                price = float(data['last_price'])
                change = float(data['percent_change_24h'])
                direction = "📈 Купити" if change > 0 else "📉 Продати"
                return f"🟡 Bybit {symbol}\nЦіна: {price:.2f}\nЗміна: {change:.2f}% → {direction}"
        return "Монету не знайдено."
    except Exception as e:
        return f"❌ Помилка з Bybit: {e}"

# Команда старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(symbol[:-4], callback_data=symbol)] for symbol in SPOT_PAIRS]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("💰 Обери монету для сигналу:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("💰 Обери монету для сигналу:", reply_markup=reply_markup)


# Обробка кнопки вибору монети
async def coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data

    keyboard = [
        [
            InlineKeyboardButton("Binance", callback_data=f"binance|{symbol}"),
            InlineKeyboardButton("Bybit", callback_data=f"bybit|{symbol}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🔍 Обрана монета: {symbol}\nОбери біржу:", reply_markup=reply_markup)

# Обробка вибору біржі
async def exchange_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exchange, symbol = query.data.split("|")

    if exchange == "binance":
        text = get_binance_signal(symbol)
    else:
        text = get_bybit_signal(symbol)

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=symbol)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

# Обробка повернення до меню монет
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update.callback_query, context)


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(exchange_selected, pattern=r"^(binance|bybit)\|"))
    app.add_handler(CallbackQueryHandler(coin_selected, pattern=r"^[A-Z]+USDT$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern=r"^back_to_menu$"))

    print("✅ Бот запущено")
    app.run_polling()
