from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from database import Database
from ai import AIRecommender

(
    ROLE,
    SUP_NAME, SUP_COMPANY, SUP_MATERIAL, SUP_PRICE, SUP_CONTACT, SUP_LOCATION,
    BUY_NAME, BUY_COMPANY,
    ORDER_SUPPLIER, ORDER_MATERIAL, ORDER_QUANTITY,
    ADMIN_ACTION, AI_MATERIAL, AI_LOCATION
) = range(15)

MAIN_MENU = [
    ["🏗 Register as Supplier", "🛒 Register as Buyer"],
    ["📦 View Suppliers", "📋 My Orders"],
    ["🤖 AI Recommend", "🛒 Place Order"],
    ["🔧 Admin Panel"]
]

db = Database()
ai = AIRecommender(db)


class BotHandlers:

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text(
            "👷 Welcome to *QurilishLink*\n"
            "Uzbekistan's Construction Procurement Bot!\n\n"
            "Connecting construction firms with trusted suppliers.\n\n"
            "Please choose an option:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ROLE

    @staticmethod
    async def role_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == "🏗 Register as Supplier":
            await update.message.reply_text(
                "Let's register you as a supplier.\n\nWhat is your full name?",
                reply_markup=ReplyKeyboardRemove()
            )
            return SUP_NAME
        elif text == "🛒 Register as Buyer":
            await update.message.reply_text(
                "Let's register you as a buyer.\n\nWhat is your full name?",
                reply_markup=ReplyKeyboardRemove()
            )
            return BUY_NAME
        elif text == "📦 View Suppliers":
            await BotHandlers.show_suppliers(update, context)
            return ROLE
        elif text == "📋 My Orders":
            await BotHandlers.show_my_orders(update, context)
            return ROLE
        elif text == "🤖 AI Recommend":
            await update.message.reply_text(
                "🤖 *AI Supplier Recommender*\n\n"
                "What material do you need?\n"
                "(e.g. Cement, Steel, Bricks)",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            return AI_MATERIAL
        elif text == "🛒 Place Order":
            await BotHandlers.order_start(update, context)
            return ORDER_SUPPLIER
        elif text == "🔧 Admin Panel":
            await BotHandlers.admin_panel(update, context)
            return ROLE
        else:
            await update.message.reply_text("Please choose an option from the menu.")
            return ROLE

    # ── Supplier registration ────────────────────────────
    @staticmethod
    async def sup_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_name"] = update.message.text
        await update.message.reply_text("What is your company name?")
        return SUP_COMPANY

    @staticmethod
    async def sup_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_company"] = update.message.text
        await update.message.reply_text(
            "What material do you supply?\n(e.g. Cement, Steel, Bricks, Sand, Timber)"
        )
        return SUP_MATERIAL

    @staticmethod
    async def sup_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_material"] = update.message.text
        await update.message.reply_text("What is your price per unit (in USD)?")
        return SUP_PRICE

    @staticmethod
    async def sup_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            price = float(update.message.text)
            context.user_data["sup_price"] = price
            await update.message.reply_text("What is your contact number or email?")
            return SUP_CONTACT
        except ValueError:
            await update.message.reply_text("Please enter a valid number (e.g. 25.50)")
            return SUP_PRICE

    @staticmethod
    async def sup_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_contact"] = update.message.text
        await update.message.reply_text(
            "📍 Last step! Please share your business location.\n\n"
            "Tap the 📎 paperclip icon → Location → Send your current location",
            reply_markup=ReplyKeyboardRemove()
        )
        return SUP_LOCATION

    @staticmethod
    async def sup_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.location:
            await update.message.reply_text(
                "⚠️ Please share your location using the 📎 paperclip → Location"
            )
            return SUP_LOCATION

        d = context.user_data
        db.add_supplier(
            update.effective_user.id,
            d["sup_name"], d["sup_company"],
            d["sup_material"], d["sup_price"],
            d["sup_contact"],
            update.message.location.latitude,
            update.message.location.longitude
        )
        await update.message.reply_text(
            f"✅ *Supplier Registered Successfully!*\n\n"
            f"👤 Name: {d['sup_name']}\n"
            f"🏢 Company: {d['sup_company']}\n"
            f"🧱 Material: {d['sup_material']}\n"
            f"💵 Price/unit: ${d['sup_price']}\n"
            f"📞 Contact: {d['sup_contact']}\n"
            f"📍 Location: Saved ✅",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ROLE

    # ── Buyer registration ───────────────────────────────
    @staticmethod
    async def buy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["buy_name"] = update.message.text
        await update.message.reply_text("What is your company name?")
        return BUY_COMPANY

    @staticmethod
    async def buy_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["buy_company"] = update.message.text
        d = context.user_data
        db.add_buyer(update.effective_user.id, d["buy_name"], d["buy_company"])
        await update.message.reply_text(
            f"✅ *Buyer Registered!*\n\n"
            f"👤 Name: {d['buy_name']}\n"
            f"🏢 Company: {d['buy_company']}\n\n"
            f"You can now browse suppliers and place orders!",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ROLE

    # ── View suppliers ───────────────────────────────────
    @staticmethod
    async def show_suppliers(update: Update, context: ContextTypes.DEFAULT_TYPE):
        suppliers = db.get_all_suppliers()
        if not suppliers:
            await update.message.reply_text("No suppliers registered yet.")
            return
        msg = "📦 *Available Suppliers:*\n\n"
        for s in suppliers:
            msg += (
                f"🔹 *ID: {s[0]}* — {s[2]}\n"
                f"   👤 {s[1]}\n"
                f"   🧱 Material: {s[3]}\n"
                f"   💵 Price/unit: ${s[4]}\n"
                f"   📞 Contact: {s[5]}\n\n"
            )
        msg += "To place an order type /order"
        await update.message.reply_text(msg, parse_mode="Markdown")

    # ── AI Recommendation ────────────────────────────────
    @staticmethod
    async def ai_recommend_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        material = update.message.text
        context.user_data["ai_material"] = material
        await update.message.reply_text(
            f"📍 Now share YOUR location so I can find the closest *{material}* supplier!\n\n"
            f"Tap the 📎 paperclip → Location → Send your location",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return AI_LOCATION

    @staticmethod
    async def ai_recommend_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.location:
            await update.message.reply_text(
                "⚠️ Please share your location using the 📎 paperclip → Location"
            )
            return AI_LOCATION

        buyer_lat = update.message.location.latitude
        buyer_lon = update.message.location.longitude
        material = context.user_data.get("ai_material", "")

        if not material:
            await update.message.reply_text(
                "❌ Something went wrong. Please start again.",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
            )
            return ROLE

        best, reason = ai.recommend_supplier(material, buyer_lat, buyer_lon)

        if not best:
            await update.message.reply_text(
                f"❌ No suppliers found for *{material}*.",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
            )
            return ROLE

        price_analysis = ai.analyze_price(material, best[4])
        await update.message.reply_text(
            f"🤖 *AI Recommendation for {material}:*\n\n"
            f"🏆 Best Supplier: *{best[2]}*\n"
            f"👤 {best[1]}\n"
            f"💵 Price: ${best[4]}/unit\n"
            f"📞 {best[5]}\n\n"
            f"📌 Why recommended:\n{reason}\n\n"
            f"{price_analysis}",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        )
        return ROLE

    # ── Place order ──────────────────────────────────────
    @staticmethod
    async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        suppliers = db.get_all_suppliers()
        if not suppliers:
            await update.message.reply_text("No suppliers available yet.")
            return ConversationHandler.END
        msg = "Enter the *Supplier ID* to order from:\n\n"
        for s in suppliers:
            msg += f"ID {s[0]}: {s[2]} — {s[3]}\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return ORDER_SUPPLIER

    @staticmethod
    async def order_supplier(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            sup_id = int(update.message.text)
            supplier = db.get_supplier_by_id(sup_id)
            if not supplier:
                await update.message.reply_text("Supplier not found. Enter a valid ID.")
                return ORDER_SUPPLIER
            context.user_data["order_supplier_id"] = supplier[0]
            context.user_data["order_supplier_name"] = supplier[2]
            await update.message.reply_text(
                f"Ordering from *{supplier[2]}*\n\nWhat material do you need?",
                parse_mode="Markdown"
            )
            return ORDER_MATERIAL
        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ORDER_SUPPLIER

    @staticmethod
    async def order_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["order_material"] = update.message.text
        await update.message.reply_text("How many units do you need?")
        return ORDER_QUANTITY

    @staticmethod
    async def order_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            qty = int(update.message.text)
            d = context.user_data
            buyer_name = db.get_buyer_name(update.effective_user.id)
            supplier = db.get_supplier_by_id(d["order_supplier_id"])
            price_per_unit = supplier[4] if supplier else 0
            commission = db.add_order(
                   update.effective_user.id, buyer_name,
                   d["order_supplier_id"], d["order_supplier_name"],
                   d["order_material"], qty, price_per_unit
                ) 
            total_cost = round(qty * price_per_unit, 2)
            await update.message.reply_text(
               f"✅ *Order Placed!*\n\n"
               f"🏢 Supplier: {d['order_supplier_name']}\n"
               f"🧱 Material: {d['order_material']}\n"
               f"📦 Quantity: {qty} units\n"
               f"💵 Price/unit: ${price_per_unit}\n"
               f"💰 Total Cost: ${total_cost}\n"
               f"📊 Platform Fee (2%): ${commission}\n"
               f"📋 Status: Pending",
               parse_mode="Markdown",
               reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
)
            return ROLE
        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ORDER_QUANTITY

    # ── My orders ────────────────────────────────────────
    @staticmethod
    async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        orders = db.get_buyer_orders(update.effective_user.id)
        if not orders:
            await update.message.reply_text("You have no orders yet!")
            return
        msg = "📋 *Your Orders:*\n\n"
        for o in orders:
            msg += (
                f"🔹 Order #{o[0]}\n"
                f"   🏢 Supplier: {o[1]}\n"
                f"   🧱 Material: {o[2]}\n"
                f"   📦 Quantity: {o[3]} units\n"
                f"   📊 Status: {o[4]}\n"
                f"   🕐 Placed: {o[5]}\n\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")

    # ── Admin panel ──────────────────────────────────────
    @staticmethod
    async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        suppliers, buyers, orders, pending = db.get_stats()
        revenue = db.get_total_revenue()
        all_orders = db.get_all_orders()
        msg = (
            f"🔧 *QurilishLink Admin Dashboard*\n\n"
            f"📊 *Statistics:*\n"
            f"   🏗 Suppliers: {suppliers}\n"
            f"   🛒 Buyers: {buyers}\n"
            f"   📦 Total Orders: {orders}\n"
            f"   ⏳ Pending: {pending}\n"
            f"   💰 Total Revenue: ${revenue}\n\n"
            f"📋 *All Orders:*\n\n"
            
        )
        if all_orders:
            for o in all_orders:
                msg += (
                    f"Order #{o[0]}: {o[1]} → {o[2]}\n"
                    f"   🧱 {o[3]} | 📦 {o[4]} units | 📊 {o[5]}\n"
                    f"   🕐 {o[6]}\n\n"
                )
        else:
            msg += "No orders yet.\n"
        await update.message.reply_text(msg, parse_mode="Markdown")