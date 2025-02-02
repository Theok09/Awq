import re
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackContext, ConversationHandler)

# ================= تنظیمات پیشرفته =====================
TOKEN = "YOUR_BOT_TOKEN"
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc"
GOLD_API_URL = "https://api.tgju.org/v1/data/sana/parameters"
BLOCKCHAIN_APIS = {
    'ETH': {'url': 'https://api.etherscan.io/api', 'key': 'YOUR_ETHERSCAN_KEY'},
    'BTC': {'url': 'https://blockchain.info/rawaddr/'},
    'SOL': {'url': 'https://public-api.solscan.io/account/'}
}

# ================= سیستم پردازش زبان طبیعی =====================
def natural_language_processor(text: str):
    text = text.lower().strip()
    
    # تشخیص ارزهای دیجیتال
    crypto_patterns = {
        r'(\d+[\.,]?\d*)\s*(بیت[ _]?کوین|btc|bitcoin)': 'bitcoin',
        r'(\d+[\.,]?\d*)\s*(اتریوم|eth|ether)': 'ethereum',
        r'(\d+[\.,]?\d*)\s*(سولانا|sol|solana)': 'solana',
        r'(\d+[\.,]?\d*)\s*(تتر|usdt|tether)': 'tether',
    }
    
    # تشخیص طلا و سکه
    gold_patterns = {
        r'(طلای|طلا)\s*(\d+[\.,]?\d*)?': 'geram18',
        r'(سکه|آزادی|بهرام)\s*(\d+[\.,]?\d*)?': 'sekeb',
        r'(مثقال|مثقالی)\s*(\d+[\.,]?\d*)?': 'mesghal'
    }
    
    # بررسی الگوهای ارز دیجیتال
    for pattern, coin_id in crypto_patterns.items():
        match = re.match(pattern, text)
        if match:
            amount = float(match.group(1).replace(',', '.')) if match.group(1) else 1.0
            return {'type': 'crypto', 'id': coin_id, 'amount': amount}
    
    # بررسی الگوهای طلا و سکه
    for pattern, item_key in gold_patterns.items():
        match = re.match(pattern, text)
        if match:
            amount = float(match.group(2).replace(',', '.')) if match.group(2) else 1.0
            return {'type': 'gold', 'key': item_key, 'amount': amount}
    
    return None

# ================= سیستم قیمت‌گذاری پیشرفته =====================
class AdvancedPriceChecker:
    @staticmethod
    def get_crypto_price(coin_id: str, amount: float=1):
        try:
            params = {'ids': coin_id, 'vs_currency': 'usd'}
            response = requests.get(CRYPTO_API_URL, params=params)
            data = response.json()
            
            if data and isinstance(data, list):
                coin = data[0]
                return {
                    'name': coin['name'],
                    'symbol': coin['symbol'],
                    'price': coin['current_price'],
                    'change_24h': coin['price_change_percentage_24h'],
                    'high_24h': coin['high_24h'],
                    'low_24h': coin['low_24h'],
                    'amount': amount,
                    'total': amount * coin['current_price']
                }
        except Exception as e:
            print(f"Error fetching crypto price: {e}")
            return None

    @staticmethod
    def get_gold_price(item_key: str, amount: float=1):
        try:
            response = requests.get(GOLD_API_URL)
            data = response.json()
            
            for item in data.values():
                if item.get('key') == item_key:
                    price = float(item['price'].replace(',', ''))
                    return {
                        'title': item['title'],
                        'price': price,
                        'change': item['change'],
                        'amount': amount,
                        'total': amount * price
                    }
            return None
        except Exception as e:
            print(f"Error fetching gold price: {e}")
            return None

# ================= دسترسی به اطلاعات بلاکچین =====================
class BlockchainAnalyzer:
    @staticmethod
    def get_wallet_info(platform: str, address: str):
        try:
            if platform == 'ETH':
                url = f"{BLOCKCHAIN_APIS['ETH']['url']}?module=account&action=balance&address={address}&tag=latest&apikey={BLOCKCHAIN_APIS['ETH']['key']}"
                response = requests.get(url)
                balance = int(response.json()['result']) / 10**18
                return f"موجودی اتریوم: {balance:.4f} ETH"
            
            elif platform == 'BTC':
                url = f"{BLOCKCHAIN_APIS['BTC']['url']}{address}"
                response = requests.get(url)
                data = response.json()
                balance = data['final_balance'] / 10**8
                return f"موجودی بیت‌کوین: {balance:.8f} BTC"
            
            elif platform == 'SOL':
                url = f"{BLOCKCHAIN_APIS['SOL']['url']}{address}"
                response = requests.get(url)
                data = response.json()
                balance = data['tokenInfo']['tokenAmount']['amount'] / 10**9
                return f"موجودی سولانا: {balance:.2f} SOL"
            
        except Exception as e:
            return f"خطا در دریافت اطلاعات: {str(e)}"

# ================= کنترلرهای ربات =====================
def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user = update.message.from_user
    
    # پردازش زبان طبیعی
    nlp_result = natural_language_processor(text)
    
    if not nlp_result:
        update.message.reply_text("⚠️ لطفاً درخواست خود را به شکل صحیح وارد کنید. مثال:\n• 2 سولانا\n• طلا\n• 1.5 بیت‌کوین")
        return
    
    if nlp_result['type'] == 'crypto':
        result = AdvancedPriceChecker.get_crypto_price(nlp_result['id'], nlp_result['amount'])
        if result:
            message = (
                f"💰 {result['name']} ({result['symbol'].upper()})\n\n"
                f"مقدار: {nlp_result['amount']}\n"
                f"قیمت واحد: ${result['price']:,.2f}\n"
                f"جمع کل: ${result['total']:,.2f}\n\n"
                f"تغییرات 24h: {result['change_24h']:.2f}%\n"
                f"بالاترین قیمت: ${result['high_24h']:,.2f}\n"
                f"پایین‌ترین قیمت: ${result['low_24h']:,.2f}"
            )
        else:
            message = "⚠️ اطلاعات ارز مورد نظر یافت نشد"
    
    elif nlp_result['type'] == 'gold':
        result = AdvancedPriceChecker.get_gold_price(nlp_result['key'], nlp_result['amount'])
        if result:
            message = (
                f"🏅 {result['title']}\n\n"
                f"مقدار: {nlp_result['amount']}\n"
                f"قیمت واحد: {result['price']:,.0f} تومان\n"
                f"جمع کل: {result['total']:,.0f} تومان\n\n"
                f"تغییرات: {result['change']}%"
            )
        else:
            message = "⚠️ اطلاعات طلای مورد نظر یافت نشد"
    
    update.message.reply_text(message)

def wallet_handler(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 2:
        update.message.reply_text("⚠️ فرمت صحیح:\n/wallet [پلتفرم] [آدرس]")
        return
    
    platform, address = args
    platform = platform.upper()
    
    if platform not in BLOCKCHAIN_APIS:
        update.message.reply_text("⚠️ پلتفرم‌های پشتیبانی شده: ETH, BTC, SOL")
        return
    
    result = BlockchainAnalyzer.get_wallet_info(platform, address)
    update.message.reply_text(result)

# ================= راه‌اندازی ربات =====================
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CommandHandler("wallet", wallet_handler))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
