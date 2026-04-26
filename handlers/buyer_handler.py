from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start_handler import (
    ROLE_CHOICE, BUY_NAME, BUY_COMPANY,
    ORDER_SUPPLIER, ORDER_PRODUCT, ORDER_QUANTITY,
    AI_MATERIAL, AI_LOCATION,
    BUYER_MENU
)


class BuyerHandler:
    def __init__(self, database):
        self.db = database
        self.ai = None

    def set_ai(self, ai):
        self.ai = ai

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == "🔍 View Suppliers":
            return await self.view_suppliers(update, context)
        elif text == "🛒 Place Order":
            return await self.place_order_start(update, context)
        elif text == "🤖 AI Recommend":
            return await self.ai_start(update, context)
        elif text == "📋 My Orders":
            return await self.my_orders(update, context)
        elif text == "🏠 Main Menu":
            await update.message.reply_text(
                "Main menu:",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE
        else:
            await update.message.reply_text(
                "Please choose an option from the menu.",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

    # ── Registration ─────────────────────────────────────────────────────
    async def buy_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["buy_name"] = update.message.text
        await update.message.reply_text("What is your company name?")
        return BUY_COMPANY

    async def buy_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["buy_company"] = update.message.text
        d = context.user_data

        self.db.add_buyer(update.effective_user.id, d["buy_name"], d["buy_company"])
        self.db.register_user(
            update.effective_user.id,
            d["buy_name"], d["buy_company"], "buyer"
        )

        await update.message.reply_text(
            f"✅ *Buyer Registered!*\n\n"
            f"👤 Name: {d['buy_name']}\n"
            f"🏢 Company: {d['buy_company']}\n\n"
            f"You can now browse suppliers and place orders!",
            parse_mode="Markdown",
            reply_markup=BUYER_MENU
        )
        return ROLE_CHOICE

    # ── View Suppliers ───────────────────────────────────────────────────
    async def view_suppliers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        suppliers = self.db.get_all_suppliers()

        if not suppliers:
            await update.message.reply_text(
                "No suppliers registered yet.",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        msg = "📦 *Available Suppliers:*\n\n"
        for s in suppliers:
            products = self.db.get_supplier_products(s[0])
            msg += f"🏢 *{s[2]}* (ID: {s[0]})\n"
            msg += f"   👤 {s[1]}\n"
            msg += f"   📞 {s[3]}\n"
            if products:
                msg += f"   📦 *Products:*\n"
                for p in products:
                    msg += f"      • {p[1]} — ${p[2]}/{p[3]}\n"
            msg += "\n"

        msg += "To place an order tap 🛒 Place Order"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=BUYER_MENU)
        return ROLE_CHOICE

    # ── Place Order ──────────────────────────────────────────────────────
    async def place_order_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        suppliers = self.db.get_all_suppliers()

        if not suppliers:
            await update.message.reply_text(
                "No suppliers available yet.",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        msg = "🛒 *Select a Supplier:*\n\n"
        for s in suppliers:
            products = self.db.get_supplier_products(s[0])
            msg += f"*ID {s[0]}* — {s[2]}\n"
            for p in products:
                msg += f"   • {p[1]} — ${p[2]}/{p[3]}\n"
            msg += "\n"

        msg += "Enter the *Supplier ID* to order from:"
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return ORDER_SUPPLIER

    async def order_supplier(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            sup_id = int(update.message.text)
            supplier = self.db.get_supplier_by_id(sup_id)

            if not supplier:
                await update.message.reply_text("Supplier not found. Please enter a valid ID.")
                return ORDER_SUPPLIER

            products = self.db.get_supplier_products(sup_id)
            if not products:
                await update.message.reply_text(
                    "This supplier has no products listed.",
                    reply_markup=BUYER_MENU
                )
                return ROLE_CHOICE

            context.user_data["order_supplier_id"] = sup_id
            context.user_data["order_supplier_name"] = supplier[2]

            msg = f"📦 *Products from {supplier[2]}:*\n\n"
            for p in products:
                msg += f"*ID {p[0]}* — {p[1]}\n"
                msg += f"   💵 ${p[2]}/{p[3]}\n\n"

            msg += "Enter the *Product ID* you want to order:"
            await update.message.reply_text(msg, parse_mode="Markdown")
            return ORDER_PRODUCT

        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ORDER_SUPPLIER

    async def order_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            product_id = int(update.message.text)
            product = self.db.get_product_by_id(product_id)

            if not product or product[1] != context.user_data["order_supplier_id"]:
                await update.message.reply_text("Product not found. Please enter a valid Product ID.")
                return ORDER_PRODUCT

            context.user_data["order_product_id"] = product_id
            context.user_data["order_material"] = product[2]
            context.user_data["order_price"] = product[3]
            context.user_data["order_unit"] = product[4]

            await update.message.reply_text(
                f"🧱 *{product[2]}* — ${product[3]}/{product[4]}\n\n"
                f"How many units do you need?",
                parse_mode="Markdown"
            )
            return ORDER_QUANTITY

        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ORDER_PRODUCT

    async def order_quantity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            qty = int(update.message.text)
            d = context.user_data
            buyer_name = self.db.get_buyer_name(update.effective_user.id)

            commission, total_cost = self.db.add_order(
                update.effective_user.id, buyer_name,
                d["order_supplier_id"], d["order_supplier_name"],
                d["order_product_id"], d["order_material"],
                qty, d["order_price"]
            )

            await update.message.reply_text(
                f"✅ *Order Placed Successfully!*\n\n"
                f"🏢 Supplier: {d['order_supplier_name']}\n"
                f"🧱 Material: {d['order_material']}\n"
                f"📦 Quantity: {qty} {d['order_unit']}\n"
                f"💵 Price/unit: ${d['order_price']}\n"
                f"💰 Total Cost: ${total_cost}\n"
                f"📊 Platform Fee (2%): ${commission}\n"
                f"📋 Status: Pending",
                parse_mode="Markdown",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ORDER_QUANTITY

    # ── My Orders ────────────────────────────────────────────────────────
    async def my_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        orders = self.db.get_buyer_orders(update.effective_user.id)

        if not orders:
            await update.message.reply_text(
                "You have no orders yet!",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        msg = "📋 *Your Orders:*\n\n"
        for o in orders:
            msg += (
                f"🔹 Order #{o[0]}\n"
                f"   🏢 Supplier: {o[1]}\n"
                f"   🧱 Material: {o[2]}\n"
                f"   📦 Quantity: {o[3]} units\n"
                f"   💰 Total: ${o[5]}\n"
                f"   📊 Status: {o[7]}\n"
                f"   🕐 {o[8]}\n\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=BUYER_MENU)
        return ROLE_CHOICE

    # ── AI Recommend ─────────────────────────────────────────────────────
    async def ai_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *AI Supplier Recommender*\n\n"
            "What material do you need?\n"
            "(e.g. Cement, Steel, Bricks)",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return AI_MATERIAL

    async def ai_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["ai_material"] = update.message.text
        await update.message.reply_text(
            f"📍 Share your location so I can find the closest supplier!\n\n"
            f"Tap 📎 → Location → Send your location",
            reply_markup=ReplyKeyboardRemove()
        )
        return AI_LOCATION

    async def ai_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.location:
            await update.message.reply_text(
                "⚠️ Please share your location using 📎 → Location"
            )
            return AI_LOCATION

        buyer_lat = update.message.location.latitude
        buyer_lon = update.message.location.longitude
        material = context.user_data.get("ai_material", "")

        if not self.ai:
            from ai import AIRecommender
            self.ai = AIRecommender(self.db)

        best, reason = self.ai.recommend_supplier(material, buyer_lat, buyer_lon)

        if not best:
            await update.message.reply_text(
                f"❌ No suppliers found for *{material}*.",
                parse_mode="Markdown",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        # Get products for recommended supplier
        products = self.db.get_supplier_products(best[0])
        products_msg = ""
        for p in products:
            if material.lower() in p[1].lower():
                products_msg += f"   • {p[1]} — ${p[2]}/{p[3]}\n"

        await update.message.reply_text(
            f"🤖 *Best Supplier for {material}:*\n\n"
            f"🏆 *{best[2]}*\n"
            f"👤 {best[1]}\n"
            f"📞 {best[3]}\n\n"
            f"📦 *Matching Products:*\n{products_msg}\n"
            f"📌 *Why recommended:*\n{reason}",
            parse_mode="Markdown",
            reply_markup=BUYER_MENU
        )
        return ROLE_CHOICE