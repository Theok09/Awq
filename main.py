
import logging
import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Configurations
TOKEN = "7354915525:AAEjyAR25B-Cw9KVxqQ0z-U9jartMz2HTFg"
ADMIN_ID = 6098807937  # Replace with your Telegram ID
DATABASE_FILE = 'database.json'
WALLETS_FILE = 'wallets.json'

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Utility Functions ---
def load_wallets():
    with open(WALLETS_FILE, 'r') as file:
        return json.load(file)

def save_wallets(wallets):
    with open(WALLETS_FILE, 'w') as file:
        json.dump(wallets, file, indent=4)

def load_investments():
    with open(DATABASE_FILE, 'r') as file:
        return json.load(file)

def save_investments(data):
    with open(DATABASE_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 TRON", callback_data='deposit_tron')],
        [InlineKeyboardButton("💵 USDT", callback_data='deposit_usdt')],
        [InlineKeyboardButton("🪙 Litecoin", callback_data='deposit_ltc')],
        [InlineKeyboardButton("💼 Withdraw Funds", callback_data='withdraw')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Welcome to the Investment Bot!\n\n"
        "Please select an option:",
        reply_markup=reply_markup
    )

# --- Deposit Handling ---
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    currency = query.data.split('_')[1]
    context.user_data['currency'] = currency
    wallets = load_wallets()
    wallet_address = wallets.get(currency, 'Wallet address not set')
    
    await query.message.reply_text(
        f"💼 Deposit Address for {currency.upper()}:\n`{wallet_address}`\n\n"
        "📥 After depositing, send your Transaction ID (TxID) to confirm your deposit."
    )

# --- Confirm Deposit ---
async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    user_id = update.message.from_user.id
    currency = context.user_data.get('currency')
    
    if not currency:
        await update.message.reply_text("❗ Please select a cryptocurrency first!")
        return
    
    # Verify Transaction (Example API Call)
    if currency == 'tron':
        response = requests.get(f"https://api.trongrid.io/v1/transactions/{txid}")
    elif currency == 'usdt':
        response = requests.get(f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={txid}&apikey=YOUR_ETHERSCAN_API_KEY")
    else:
        await update.message.reply_text("❗ Unsupported currency for transaction verification.")
        return
    
    if response.status_code == 200 and 'success' in response.text:
        amount = 100  # Placeholder: You should parse the amount from the API response
        return_date = datetime.now() + timedelta(weeks=2)
        
        investments = load_investments()
        investments[user_id] = {
            'currency': currency,
            'amount': amount,
            'return_date': return_date.strftime('%Y-%m-%d'),
            'profit': amount * 1.10,
            'txid': txid
        }
        save_investments(investments)
        
        await update.message.reply_text(
            f"✅ **Deposit Confirmed!**\n\n"
            f"💵 Amount: {amount} {currency.upper()}\n"
            f"📅 Return Date: {return_date.strftime('%Y-%m-%d')}\n"
            f"💰 Total Return: {amount * 1.10} {currency.upper()}"
        )
    else:
        await update.message.reply_text("❗ Invalid or unverified transaction ID. Please try again.")

# --- Withdrawal Handling ---
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.
