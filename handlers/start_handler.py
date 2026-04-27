from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

ADMIN_ID = 507360653

(
    ROLE_CHOICE,
    SUP_NAME, SUP_COMPANY, SUP_CONTACT, SUP_LOCATION, SUP_DELIVERY,
    SUP_PRODUCT_MATERIAL, SUP_PRODUCT_DESC, SUP_PRODUCT_PRICE, SUP_PRODUCT_UNIT, SUP_PRODUCT_STOCK, SUP_MORE_PRODUCTS,
    SUP_SELECT_PRODUCT, SUP_UPDATE_STOCK,
    SUP_SELECT_ORDER, SUP_UPDATE_DELIVERY,
    BUY_NAME, BUY_COMPANY,
    ORDER_SUPPLIER, ORDER_PRODUCT, ORDER_QUANTITY, ORDER_DELIVERY, ORDER_PAYMENT,
    AI_MATERIAL, AI_LOCATION,
    ADMIN_ACTION
) = range(26)

SUPPLIER_MENU = ReplyKeyboardMarkup([
    ["📦 My Products", "➕ Add Product"],
    ["📋 My Orders Received", "📊 My Stats"],
    ["📊 Update Stock", "🚚 Update Delivery"],
    ["🌐 My Dashboard", "🏠 Main Menu"]
], resize_keyboard=True)

SUPPLIER_MENU_ADMIN = SUPPLIER_MENU

BUYER_MENU = ReplyKeyboardMarkup([
    ["🔍 View Suppliers", "🛒 Place Order"],
    ["🤖 AI Recommend", "📋 My Orders"],
    ["🌐 Track Orders", "🏠 Main Menu"]
], resize_keyboard=True)

BUYER_MENU_ADMIN = BUYER_MENU

ADMIN_MENU = ReplyKeyboardMarkup([
    ["📊 Admin Dashboard", "📦 All Orders"],
    ["👥 All Users", "💰 Revenue Report"],
], resize_keyboard=True)


def get_supplier_menu(telegram_id):
    return SUPPLIER_MENU


def get_buyer_menu(telegram_id):
    return BUYER_MENU


class StartHandler:
    def __init__(self, database):
        self.db = database

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        telegram_id = update.effective_user.id
        role = self.db.get_user_role(telegram_id)

        if role == "supplier":
            await update.message.reply_text(
                "👷 Welcome back to *QurilishLink*!\n\n"
                "You are registered as a *Supplier*.\n"
                "Manage your products and orders below:",
                parse_mode="Markdown",
                reply_markup=SUPPLIER_MENU
            )
            return ROLE_CHOICE

        elif role == "buyer":
            await update.message.reply_text(
                "🛒 Welcome back to *QurilishLink*!\n\n"
                "You are registered as a *Buyer*.\n"
                "Find suppliers and place orders below:",
                parse_mode="Markdown",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        else:
            if telegram_id == ADMIN_ID:
                await update.message.reply_text(
                    "🔧 *QurilishLink Admin Panel*\n\nWelcome back, Admin!",
                    parse_mode="Markdown",
                    reply_markup=ADMIN_MENU
                )
                return ADMIN_ACTION

            keyboard = [["🏗 Register as Supplier", "🛒 Register as Buyer"]]
            await update.message.reply_text(
                "👷 Welcome to *QurilishLink*\n"
                "Uzbekistan's Construction Procurement Platform!\n\n"
                "Connecting construction firms with trusted suppliers.\n\n"
                "Please choose your role:",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return ROLE_CHOICE

    async def role_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return ROLE_CHOICE
        text = update.message.text
        telegram_id = update.effective_user.id
        role = self.db.get_user_role(telegram_id)

        if text == "🔧 Admin Panel":
            if telegram_id != ADMIN_ID:
                await update.message.reply_text("⛔ Access denied.")
                return ROLE_CHOICE
            await update.message.reply_text(
                "🔧 *Admin Panel*\nWelcome, Admin!",
                parse_mode="Markdown",
                reply_markup=ADMIN_MENU
            )
            return ADMIN_ACTION

        if text == "🏗 Register as Supplier":
            await update.message.reply_text(
                "Let's register you as a supplier.\n\nWhat is your full name?",
                reply_markup=ReplyKeyboardRemove()
            )
            return SUP_NAME

        if text == "🛒 Register as Buyer":
            await update.message.reply_text(
                "Let's register you as a buyer.\n\nWhat is your full name?",
                reply_markup=ReplyKeyboardRemove()
            )
            return BUY_NAME

        if role == "supplier":
            from handlers.supplier_handler import SupplierHandler
            handler = SupplierHandler(self.db)
            return await handler.handle(update, context)

        if role == "buyer":
            from handlers.buyer_handler import BuyerHandler
            handler = BuyerHandler(self.db)
            return await handler.handle(update, context)

        await update.message.reply_text("Please choose an option from the menu.")
        return ROLE_CHOICE