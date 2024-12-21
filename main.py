import logging
import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- Configuration ---
TOKEN = "7354915525:AAEjyAR25B-Cw9KVxqQ0z-U9jartMz2HTFg"
ADMIN_ID = 6098807937  # Replace with your Telegram ID
DATABASE_FILE = "database.json"
WALLETS_FILE = "wallets.json"

# --- Logger Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Utility Functions ---
def load_wallets():
    try:
        with open(WALLETS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"tron": "", "usdt": "", "ltc": ""}


def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as file:
        json.dump(wallets, file, indent=4)


def load_investments():
    try:
        with open(DATABASE_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_investments(data):
    with open(DATABASE_FILE, "w") as file:
        json.dump(data, file, indent=4)


# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 TRON", callback_data="deposit_tron")],
        [InlineKeyboardButton("💵 USDT", callback_data="deposit_usdt")],
        [InlineKeyboardButton("🪙 Litecoin", callback_data="deposit_ltc")],
        [InlineKeyboardButton("💼 Withdraw Funds", callback_data="withdraw")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 **Welcome to the Investment Bot!**\n\n"
        "Please select an option to proceed:",
        reply_markup=reply_markup,
    )


# --- Deposit Handling ---
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    currency = query.data.split("_")[1]
    context.user_data["currency"] = currency
    wallets = load_wallets()
    wallet_address = wallets.get(currency, "Wallet address not set")

    await query.message.reply_text(
        f"💼 **Deposit Address for {currency.upper()}**:\n`{wallet_address}`\n\n"
        "📥 After depositing, please send your **Transaction ID (TxID)** to confirm your deposit."
    )


# --- Confirm Deposit ---
async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    user_id = update.message.from_user.id
    currency = context.user_data.get("currency")

    if not currency:
        await update.message.reply_text("❗ Please select a cryptocurrency first!")
        return

    try:
        if currency == "tron":
            response = requests.get(
                f"https://api.trongrid.io/v1/transactions/{txid}"
            )
        elif currency == "usdt":
            response = requests.get(
                f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={txid}&apikey=YOUR_ETHERSCAN_API_KEY"
            )
        else:
            await update.message.reply_text("❗ Unsupported currency for transaction verification.")
            return

        if response.status_code == 200 and response.json().get('success', False):
            amount = 100  # Placeholder: Parse the actual amount from the API response.
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

    except requests.exceptions.RequestException as e:
        logger.error(e)
        await update.message.reply_text("❗ Error verifying the transaction. Please try again later.")


# --- Withdrawal Handling ---
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    investments = load_investments()

    if user_id not in investments:
        await update.callback_query.message.reply_text("❗ No active investments found.")
        return

    investment = investments[user_id]
    return_date = datetime.strptime(investment['return_date'], '%Y-%m-%d')

    if datetime.now() >= return_date:
        del investments[user_id]
        save_investments(investments)

        await update.callback_query.message.reply_text(
            f"✅ **Withdrawal Successful!**\n\n"
            f"💵 Amount Withdrawn: {investment['profit']} {investment['currency'].upper()}"
        )
    else:
        await update.callback_query.message.reply_text(
            f"❗ Withdrawal not available until {return_date.strftime('%Y-%m-%d')}."
        )


# --- Admin Dashboard ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You do not have access to the admin panel!")
        return

    investments = load_investments()
    report = "📊 **Investment Report:**\n\n"
    for uid, data in investments.items():
        report += f"👤 User ID: {uid}\n"
        report += f"💵 Amount: {data['amount']} {data['currency'].upper()}\n"
        report += f"📅 Return Date: {data['return_date']}\n"
        report += f"💰 Total Return: {data['profit']} {data['currency'].upper()}\n"
        report += f"🔗 TxID: {data['txid']}\n\n"

    await update.message.reply_text(report if investments else "📭 No investments found.")


# --- Main Function ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(deposit, pattern="^deposit_"))
    app.add_handler(CallbackQueryHandler(withdraw, pattern="^withdraw"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_deposit))

    logger.info("🚀 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
