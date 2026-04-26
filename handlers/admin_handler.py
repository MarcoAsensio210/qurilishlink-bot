from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from handlers.start_handler import ROLE_CHOICE, ADMIN_ACTION, ADMIN_MENU

ADMIN_ID = 507360653
MINIAPP_URL = "https://marcoasensio210.github.io/qurilishlink-bot/miniapp/index.html"


class AdminHandler:
    def __init__(self, database):
        self.db = database

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id

        if telegram_id != ADMIN_ID:
            await update.message.reply_text("⛔ Access denied.")
            return ROLE_CHOICE

        text = update.message.text

        if text == "📊 Admin Dashboard":
            return await self.dashboard(update, context)
        elif text == "📦 All Orders":
            return await self.all_orders(update, context)
        elif text == "👥 All Users":
            return await self.all_users(update, context)
        elif text == "💰 Revenue Report":
            return await self.revenue_report(update, context)
        elif text == "🔙 Back":
            role = self.db.get_user_role(telegram_id)
            from handlers.start_handler import SUPPLIER_MENU, BUYER_MENU
            menu = SUPPLIER_MENU if role == "supplier" else BUYER_MENU
            await update.message.reply_text("Back to main menu:", reply_markup=menu)
            return ROLE_CHOICE
        else:
            await update.message.reply_text(
                "Please choose an option from the admin menu.",
                reply_markup=ADMIN_MENU
            )
            return ADMIN_ACTION

    async def dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Access denied.")
            return ROLE_CHOICE

        suppliers, buyers, orders, pending, revenue = self.db.get_stats()

        # Revenue by period
        week_rev = self.db.get_revenue_by_period("week")
        month_rev = self.db.get_revenue_by_period("month")
        year_rev = self.db.get_revenue_by_period("year")

        # Orders by period
        week_orders = len(self.db.get_orders_by_period("week"))
        month_orders = len(self.db.get_orders_by_period("month"))

        # Mini App button
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📊 Open Full Admin Panel",
                web_app=WebAppInfo(url=MINIAPP_URL)
            )
        ]])

        await update.message.reply_text(
            f"🔧 *QurilishLink Admin Dashboard*\n\n"
            f"📊 *Platform Statistics:*\n"
            f"   🏗 Total Suppliers: {suppliers}\n"
            f"   🛒 Total Buyers: {buyers}\n"
            f"   📦 Total Orders: {orders}\n"
            f"   ⏳ Pending Orders: {pending}\n\n"
            f"💰 *Revenue Summary:*\n"
            f"   📅 This Week: ${week_rev:.2f}\n"
            f"   🗓 This Month: ${month_rev:.2f}\n"
            f"   📆 This Year: ${year_rev:.2f}\n"
            f"   💵 All Time: ${revenue:.2f}\n\n"
            f"📦 *Order Activity:*\n"
            f"   Last 7 days: {week_orders} orders\n"
            f"   Last 30 days: {month_orders} orders\n\n"
            f"Tap below to open the full Admin Panel 👇",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return ADMIN_ACTION

    async def all_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Access denied.")
            return ROLE_CHOICE

        # Show filter options
        keyboard = ReplyKeyboardMarkup([
            ["📅 This Week", "🗓 This Month"],
            ["📆 This Year", "📋 All Orders"],
            ["🔙 Back to Admin"]
        ], resize_keyboard=True)

        await update.message.reply_text(
            "📦 *Filter Orders By:*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        context.user_data["waiting_order_filter"] = True
        return ADMIN_ACTION

    async def handle_order_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            return ROLE_CHOICE

        text = update.message.text
        period_map = {
            "📅 This Week": "week",
            "🗓 This Month": "month",
            "📆 This Year": "year",
            "📋 All Orders": "all"
        }

        if text == "🔙 Back to Admin":
            await update.message.reply_text("Admin menu:", reply_markup=ADMIN_MENU)
            return ADMIN_ACTION

        period = period_map.get(text, "all")
        orders = self.db.get_orders_by_period(period)
        revenue = self.db.get_revenue_by_period(period)

        if not orders:
            await update.message.reply_text(
                f"No orders found for this period.",
                reply_markup=ADMIN_MENU
            )
            return ADMIN_ACTION

        label = text.replace("📅 ", "").replace("🗓 ", "").replace("📆 ", "").replace("📋 ", "")
        msg = f"📦 *Orders — {label}:*\n"
        msg += f"Total: {len(orders)} orders | Revenue: ${revenue:.2f}\n\n"

        for o in orders[:15]:  # Show max 15
            msg += (
                f"#{o[0]} {o[2]} → {o[3]}\n"
                f"   🧱 {o[5]} | 📦 {o[6]} units | 💰 ${o[9]}\n"
                f"   📊 {o[11]} | 🕐 {o[12][:10]}\n\n"
            )

        if len(orders) > 15:
            msg += f"... and {len(orders) - 15} more orders"

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=ADMIN_MENU)
        return ADMIN_ACTION

    async def all_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Access denied.")
            return ROLE_CHOICE

        users = self.db.get_all_users()

        if not users:
            await update.message.reply_text("No users registered yet.", reply_markup=ADMIN_MENU)
            return ADMIN_ACTION

        suppliers = [u for u in users if u[3] == "supplier"]
        buyers = [u for u in users if u[3] == "buyer"]

        msg = f"👥 *All Users ({len(users)} total):*\n\n"
        msg += f"🏗 *Suppliers ({len(suppliers)}):*\n"
        for u in suppliers:
            msg += f"   • {u[1]} — {u[2]}\n"

        msg += f"\n🛒 *Buyers ({len(buyers)}):*\n"
        for u in buyers:
            msg += f"   • {u[1]} — {u[2]}\n"

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=ADMIN_MENU)
        return ADMIN_ACTION

    async def revenue_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Access denied.")
            return ROLE_CHOICE

        week_rev = self.db.get_revenue_by_period("week")
        month_rev = self.db.get_revenue_by_period("month")
        year_rev = self.db.get_revenue_by_period("year")
        all_rev = self.db.get_revenue_by_period("all")

        week_orders = len(self.db.get_orders_by_period("week"))
        month_orders = len(self.db.get_orders_by_period("month"))
        year_orders = len(self.db.get_orders_by_period("year"))
        all_orders = len(self.db.get_orders_by_period("all"))

        await update.message.reply_text(
            f"💰 *Revenue Report:*\n\n"
            f"📅 *This Week:*\n"
            f"   Orders: {week_orders} | Revenue: ${week_rev:.2f}\n\n"
            f"🗓 *This Month:*\n"
            f"   Orders: {month_orders} | Revenue: ${month_rev:.2f}\n\n"
            f"📆 *This Year:*\n"
            f"   Orders: {year_orders} | Revenue: ${year_rev:.2f}\n\n"
            f"💵 *All Time:*\n"
            f"   Orders: {all_orders} | Revenue: ${all_rev:.2f}\n\n"
            f"📊 Commission rate: 2% per transaction",
            parse_mode="Markdown",
            reply_markup=ADMIN_MENU
        )
        return ADMIN_ACTION