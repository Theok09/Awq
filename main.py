import re
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext, ConversationHandler)

# ================= تنظیمات ربات و API ها =====================
TOKEN = "7354915525:AAEjyAR25B-Cw9KVxqQ0z-U9jartMz2HTFg"
CRYPTO_API_URL = "https://one-api.ir/DigitalCurrency/?token=319633:679f69675fd2a"
GOLD_API_URL = "https://brsapi.ir/FreeTsetmcBourseApi/Api_Free_Gold_Currency_v2.json"
ETHERSCAN_API_KEY = "YOUR_ETHERSCAN_API_KEY"  # برای شبکه اتریوم

# ================= حالت‌های گفتگو =====================
# قیمت محصولات (pricer)
SELECTING_BRAND = 1
SELECTING_CATEGORY = 2
# اطلاعات ولت
WALLET_PLATFORM, WALLET_ADDRESS = range(2)

# ------------------ دستورات /start و /pricer ------------------
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text(
        f"Hello {user.first_name}! Welcome.\n\n"
        "دستورات موجود:\n"
        "• /pricer   => مشاهده قیمت محصولات\n"
        "• /wallet   => دریافت اطلاعات ولت (ETH, BTC, TRX, SOL)\n"
        "• /checktx  => بررسی لینک تراکنش\n"
        "همچنین برای دریافت اطلاعات ارز دیجیتال فقط نام یا نماد ارز (با تعداد اختیاری) را ارسال کنید.\n"
        "مثال: ۲ بیت کوین یا BTC"
    )

def pricer(update: Update, context: CallbackContext) -> int:
    keyboard = [
        ['Apple', 'Samsung', 'Xiaomi', 'Huawei', 'Sony'],
        ['Lenovo', 'Razer', 'Oppo', 'OnePlus', 'Motorola'],
        ['Google', 'LG', 'Asus', 'Vivo', 'ZTE']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please select a brand:", reply_markup=reply_markup)
    return SELECTING_BRAND

def get_price(brand: str, category: str) -> str:
    # در اینجا می‌توانید از API یا منابع مناسب جهت دریافت قیمت واقعی استفاده کنید
    return f"The price of the {category} from {brand} today is: $500 (temporary price)"

def handle_brand_selection(update: Update, context: CallbackContext) -> int:
    selected_brand = update.message.text
    context.user_data['brand'] = selected_brand
    keyboard = [
        ['Phone', 'Laptop', 'Earbuds', 'Smartwatch'],
        ['Tablet', 'Gaming Devices', 'Other Products']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(
        f"You selected the brand {selected_brand}.\nPlease choose a product category:",
        reply_markup=reply_markup
    )
    return SELECTING_CATEGORY

def handle_category_selection(update: Update, context: CallbackContext) -> int:
    selected_category = update.message.text
    selected_brand = context.user_data.get('brand', 'Unknown')
    price_info = get_price(selected_brand, selected_category)
    update.message.reply_text(
        f"Price information for the {selected_category} from {selected_brand}:\n{price_info}"
    )
    gold_info = get_gold_and_currency_prices()
    update.message.reply_text(gold_info)
    return ConversationHandler.END

def get_gold_and_currency_prices() -> str:
    try:
        response = requests.get(GOLD_API_URL, timeout=10)
        data = response.json()
        if 'status' in data and data['status'] == 'OK':
            name = data.get('name', 'Data not available')
            price = data.get('price', 'Data not available')
            change_percent = data.get('change_percent', 'Data not available')
            unit = data.get('unit', 'Data not available')
            date = data.get('date', 'Data not available')
            time_val = data.get('time', 'Data not available')
            return (f"Gold Price Update:\nDate: {date}  Time: {time_val}\n"
                    f"{name}: {price} {unit}\nChange: {change_percent}%")
        else:
            return "Sorry, couldn't fetch gold prices at the moment."
    except Exception as e:
        return f"Error occurred while fetching gold prices: {str(e)}"

# ------------------ اطلاعات ارز دیجیتال ------------------
def extract_amount_and_query(text: str):
    """
    در صورتی که عددی در ابتدای متن وجود داشته باشد،
    آن را به عنوان مقدار استخراج کرده و باقی متن جهت جستجوی ارز در نظر می‌گیرد.
    """
    text = text.strip()
    match = re.match(r'^([\d۰-۹.,]+)', text)
    amount = 1.0
    persian_digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    if match:
        num_str = match.group(1).translate(persian_digits)
        try:
            num_str = num_str.replace(",", ".")
            amount = float(num_str)
        except ValueError:
            amount = 1.0
        query = text[match.end():].strip()
    else:
        query = text
    return amount, query

def search_crypto(crypto_query: str, crypto_list: list) -> dict:
    """
    بررسی می‌کند آیا ارز دیجیتال مورد نظر در لیست دریافتی از API وجود دارد یا خیر.
    مقایسه روی سه فیلد: key، name و name_en انجام می‌شود.
    """
    query_lower = crypto_query.lower()
    for coin in crypto_list:
        key = coin.get("key", "").upper()
        name_fa = coin.get("name", "").strip().lower()
        name_en = coin.get("name_en", "").strip().lower()
        if query_lower == key.lower() or query_lower == name_fa or query_lower == name_en:
            return coin
    return None

def format_crypto_info(coin: dict, amount: float) -> str:
    price = coin.get("price", 0)
    total = price * amount
    return (
        f"💰 *{coin.get('name','N/A')} ({coin.get('name_en','N/A')})*\n\n"
        f"مقدار درخواستی: {amount}\n"
        f"قیمت واحد: ${price:,.2f}\n"
        f"جمع قیمت: ${total:,.2f}\n\n"
        f"تغییر 24 ساعته: {coin.get('percent_change_24h','N/A')}%\n"
        f"بالاترین قیمت 24 ساعته: ${coin.get('daily_high_price',0):,.2f}\n"
        f"پایین‌ترین قیمت 24 ساعته: ${coin.get('daily_low_price',0):,.2f}\n\n"
        f"حجم معاملات 24 ساعتی: ${coin.get('volume_24h',0):,.2f}\n"
        f"ارزش بازار (Market Cap): ${coin.get('market_cap',0):,.2f}\n\n"
        f"تغییرات زمانی:\n"
        f"1 ساعت: {coin.get('percent_change_1h','N/A')}% | 7 روز: {coin.get('percent_change_7d','N/A')}%\n"
        f"30 روز: {coin.get('percent_change_30d','N/A')}%\n\n"
        f"All Time High: ${coin.get('ath',0):,.2f}\n"
        f"All Time Low: ${coin.get('atl',0):,.2f}\n"
        f"رتبه: {coin.get('rank','N/A')} - تسلط بازار: {coin.get('dominance','N/A')}%"
    )

def handle_crypto_message(update: Update, context: CallbackContext):
    text = update.message.text
    if not text:
        return
    # اگر پیام شامل دستور باشد، ادامه ندهد
    if text.startswith("/"):
        return
    amount, query = extract_amount_and_query(text)
    if not query:
        update.message.reply_text("لطفاً نام یا نماد ارز دیجیتال را وارد کنید.")
        return
    try:
        response = requests.get(CRYPTO_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        # API ممکن است یک دیکشنری یا لیست برگرداند
        if isinstance(data, dict):
            crypto_list = [data]
        elif isinstance(data, list):
            crypto_list = data
        else:
            update.message.reply_text("❌ فرمت داده دریافتی از API ناشناخته است.")
            return
        coin = search_crypto(query, crypto_list)
        if coin:
            info = format_crypto_info(coin, amount)
            update.message.reply_text(info, parse_mode="Markdown")
        else:
            update.message.reply_text("❌ ارز دیجیتالی مطابق با درخواست شما پیدا نشد. لطفاً نام یا نماد را بررسی کنید.")
    except Exception as e:
        update.message.reply_text(f"⚠️ خطا در دریافت اطلاعات از API: {str(e)}")

# ------------------ بخش اطلاعات ولت (ETH, BTC, TRX, SOL) ------------------
def wallet_start(update: Update, context: CallbackContext) -> int:
    keyboard = [["ETH", "BTC", "TRX", "SOL"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("لطفاً پلتفرم مورد نظر را انتخاب کنید (ETH, BTC, TRX, SOL):", reply_markup=reply_markup)
    return WALLET_PLATFORM

def wallet_platform(update: Update, context: CallbackContext) -> int:
    platform = update.message.text.strip().upper()
    if platform not in ["ETH", "BTC", "TRX", "SOL"]:
        update.message.reply_text("لطفاً یکی از گزینه‌های ETH, BTC, TRX یا SOL را انتخاب کنید.")
        return WALLET_PLATFORM
    context.user_data['wallet_platform'] = platform
    update.message.reply_text("لطفاً آدرس ولت را وارد کنید:")
    return WALLET_ADDRESS

def wallet_address(update: Update, context: CallbackContext) -> int:
    platform = context.user_data.get('wallet_platform')
    address = update.message.text.strip()
    if platform == "ETH":
        info = get_eth_wallet_info(address)
    elif platform == "BTC":
        info = get_btc_wallet_info(address)
    elif platform == "TRX":
        info = get_tron_wallet_info(address)
    elif platform == "SOL":
        info = get_sol_wallet_info(address)
    else:
        info = "پلتفرم نامعتبر است."
    update.message.reply_text(info, parse_mode="Markdown")
    return ConversationHandler.END

def get_eth_wallet_info(address: str) -> str:
    try:
        balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
        res_balance = requests.get(balance_url, timeout=10).json()
        if res_balance.get("status") != "1":
            return "خطا در دریافت موجودی یا آدرس نامعتبر است."
        balance_eth = int(res_balance["result"]) / 10**18

        tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey={ETHERSCAN_API_KEY}"
        res_tx = requests.get(tx_url, timeout=10).json()
        txs = ""
        if res_tx.get("status") == "1":
            for tx in res_tx["result"]:
                time_str = datetime.fromtimestamp(int(tx["timeStamp"])).strftime('%Y-%m-%d %H:%M:%S')
                txs += f"\n  • {time_str}: {tx['value']} Wei از `{tx['from']}` به `{tx['to']}`"
        else:
            txs = "تراکنشی یافت نشد."
        return (f"*اطلاعات ولت ETH:*\n"
                f"آدرس: `{address}`\n"
                f"موجودی: {balance_eth:.4f} ETH\n"
                f"آخرین تراکنش‌ها:{txs}")
    except Exception as e:
        return f"خطا در دریافت اطلاعات ولت ETH: {str(e)}"

def get_btc_wallet_info(address: str) -> str:
    try:
        url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}"
        res = requests.get(url, timeout=10).json()
        if "error" in res:
            return "آدرس نامعتبر یا مشکلی در دریافت اطلاعات BTC وجود دارد."
        balance_btc = res.get("balance", 0) /
