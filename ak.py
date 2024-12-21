# 🛡️ توکن بات تلگرام
BOT_TOKEN = "7354915525:AAEjyAR25B-Cw9KVxqQ0z-U9jartMz2HTFg"

import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ⚙️ لیست ادمین‌ها
ADMINS = [6098807937]  # آیدی تلگرام ادمین‌ها

# 🗂️ اطلاعات کاربران (در دیتابیس ذخیره شود)
user_data = {}

# 💵 اطلاعات پلن‌ها و قیمت‌ها
plans = {
    "Basic": {"daily": 5, "weekly": 20, "monthly": 50},
    "Advanced": {"daily": 10, "weekly": 40, "monthly": 100},
    "Pro": {"daily": 20, "weekly": 80, "monthly": 200}
}

# 🚀 شروع بات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"registered": False}
    
    if not user_data[user_id]["registered"]:
        await update.message.reply_text(
            "👋 Welcome! Please register to continue.\n\n📝 Send your username:"
        )
        context.user_data['awaiting_username'] = True
    else:
        await main_menu(update)

# 📲 منوی اصلی
async def main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("🛒 Purchase Plan", callback_data='purchase_plan')],
        [InlineKeyboardButton("🔗 Link CNC User", callback_data='link_cnc_user')],
        [InlineKeyboardButton("👤 Account Info", callback_data='account_info')],
        [InlineKeyboardButton("💳 Payment Status", callback_data='payment_status')],
        [InlineKeyboardButton("🛠️ Support", callback_data='support')],
        [InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome back! Choose an option:",
        reply_markup=reply_markup
    )

# 📝 ذخیره اطلاعات ثبت‌نام
async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.user_data.get('awaiting_username'):
        username = update.message.text
        user_data[user_id]['username'] = username
        context.user_data['awaiting_username'] = False
        context.user_data['awaiting_wallet'] = True
        
        await update.message.reply_text(
            "✅ Username saved!\n\n💼 Now, send your wallet address:"
        )
    elif context.user_data.get('awaiting_wallet'):
        wallet = update.message.text
        user_data[user_id]['wallet'] = wallet
        user_data[user_id]['registered'] = True
        context.user_data['awaiting_wallet'] = False
        
        await update.message.reply_text(
            "🎉 Registration complete! Enjoy the services."
        )
        await main_menu(update)

# 🔘 مدیریت کلیک دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_data or not user_data[user_id]['registered']:
        await query.edit_message_text("❌ You must register first. Please restart the bot.")
        return

    if query.data == 'purchase_plan':
        plan_keyboard = [
            [InlineKeyboardButton("Basic", callback_data='plan_Basic')],
            [InlineKeyboardButton("Advanced", callback_data='plan_Advanced')],
            [InlineKeyboardButton("Pro", callback_data='plan_Pro')]
        ]
        await query.edit_message_text(
            text="🛒 Select a plan:",
            reply_markup=InlineKeyboardMarkup(plan_keyboard)
        )
    elif query.data.startswith('plan_'):
        selected_plan = query.data.split('_')[1]
        duration_keyboard = [
            [InlineKeyboardButton("Daily", callback_data=f'duration_{selected_plan}_daily')],
            [InlineKeyboardButton("Weekly", callback_data=f'duration_{selected_plan}_weekly')],
            [InlineKeyboardButton("Monthly", callback_data=f'duration_{selected_plan}_monthly')]
        ]
        await query.edit_message_text(
            text=f"⏳ You selected **{selected_plan}**. Choose a duration:",
            reply_markup=InlineKeyboardMarkup(duration_keyboard)
        )
    elif query.data.startswith('duration_'):
        _, plan, duration = query.data.split('_')
        price = plans[plan][duration]
        invoice_text = f"""
🧾 **Invoice Created!**
🔹 **Plan:** {plan}
🔹 **Duration:** {duration.capitalize()}
🔹 **Price:** €{price}
💳 Select your payment method:
"""
        payment_keyboard = [
            [InlineKeyboardButton("Litecoin", callback_data='payment_Litecoin')],
            [InlineKeyboardButton("Ethereum", callback_data='payment_Ethereum')],
            [InlineKeyboardButton("USDT TRC20 (TRX)", callback_data='payment_USDT_TRX')],
            [InlineKeyboardButton("USDT ERC20 (ETH)", callback_data='payment_USDT_ERC20')]
        ]
        await query.edit_message_text(
            text=invoice_text,
            reply_markup=InlineKeyboardMarkup(payment_keyboard)
        )
    elif query.data.startswith('payment_'):
        payment_method = query.data.split('_')[1]
        address = "Ggvky7m5UxZggzh7zuK34cj8rWcVgbza9US1n8PyGwhL"
        amount = 0.081748
        
        qr_data = f"{payment_method}: {address}?amount={amount}"
        qr_img = qrcode.make(qr_data)
        qr_bytes = BytesIO()
        qr_img.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)

        await query.message.reply_photo(
            photo=InputFile(qr_bytes, filename='payment_qr.png'),
            caption=f"✅ **Payment Method:** {payment_method}\n🔗 **Address:** {address}\n💰 **Amount:** {amount}\n📲 Scan the QR Code to complete your payment."
        )
        await query.edit_message_text(
            text="🛡️ Payment details have been sent."
        )

# ⚙️ پنل ادمین
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 You are not authorized to access this command.")
        return
    
    admin_keyboard = [
        [InlineKeyboardButton("🔨 Ban User", callback_data='admin_ban')],
        [InlineKeyboardButton("💰 Edit Plan Prices", callback_data='admin_edit_plan')]
    ]
    await update.message.reply_text(
        "⚙️ Admin Panel:",
        reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )

# 🏁 اجرای بات
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
