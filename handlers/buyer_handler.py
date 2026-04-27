from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start_handler import (
    ROLE_CHOICE, BUY_NAME, BUY_COMPANY,
    ORDER_SUPPLIER, ORDER_PRODUCT, ORDER_QUANTITY, ORDER_DELIVERY,
    AI_MATERIAL, AI_LOCATION,
    BUYER_MENU
)

BUYER_MINIAPP_URL = "https://marcoasensio210.github.io/qurilishlink-bot/miniapp/buyer.html"


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
        elif text == "🌐 Track Orders":
            return await self.open_dashboard(update, context)
        elif text == "🏠 Main Menu":
            await update.message.reply_text("Main menu:", reply_markup=BUYER_MENU)
            return ROLE_CHOICE
        else:
            await update.message.reply_text(
                "Please choose an option from the menu.",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

    # ── Mini App ─────────────────────────────────────────────────────────
    async def open_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🌐 Open Buyer Dashboard",
                web_app=WebAppInfo(url=BUYER_MINIAPP_URL)
            )
        ]])
        await update.message.reply_text(
            "📊 Open your Buyer Dashboard to track orders:",
            reply_markup=keyboard
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
        self.db.register_user(update.effective_user.id, d["buy_name"], d["buy_company"], "buyer")

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
            await update.message.reply_text("No suppliers registered yet.", reply_markup=BUYER_MENU)
            return ROLE_CHOICE

        msg = "📦 *Available Suppliers:*\n\n"
        for s in suppliers:
            products = self.db.get_supplier_products(s[0])
            delivery_icon = "🚚 Delivery available" if s[6] else "🏪 Pickup only"
            msg += f"🏢 *{s[2]}* (ID: {s[0]})\n"
            msg += f"   👤 {s[1]}\n"
            msg += f"   📞 {s[3]}\n"
            msg += f"   {delivery_icon}\n"
            if products:
                msg += f"   📦 *Products:*\n"
                for p in products:
                    stock_status = "✅" if p[5] > 0 else "❌"
                    msg += f"      • *{p[1]}* — ${p[3]}/{p[4]}\n"
                    if p[2]:
                        msg += f"        📝 {p[2]}\n"
                    msg += f"        📦 Stock: {p[5]} {p[4]} {stock_status}\n"
            msg += "\n"

        msg += "To place an order tap 🛒 Place Order"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=BUYER_MENU)
        return ROLE_CHOICE

    # ── Place Order ──────────────────────────────────────────────────────
    async def place_order_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        suppliers = self.db.get_all_suppliers()

        if not suppliers:
            await update.message.reply_text("No suppliers available yet.", reply_markup=BUYER_MENU)
            return ROLE_CHOICE

        msg = "🛒 *Select a Supplier:*\n\n"
        for s in suppliers:
            products = self.db.get_supplier_products(s[0])
            delivery_icon = "🚚" if s[6] else "🏪"
            msg += f"*ID {s[0]}* — {s[2]} {delivery_icon}\n"
            for p in products:
                stock_status = "✅" if p[5] > 0 else "❌"
                msg += f"   • {p[1]} — ${p[3]}/{p[4]} | 📦 {p[5]} {stock_status}\n"
            msg += "\n"

        msg += "Enter the Supplier ID number (e.g. type *1*):"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
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
                await update.message.reply_text("This supplier has no products.", reply_markup=BUYER_MENU)
                return ROLE_CHOICE

            context.user_data["order_supplier_id"] = sup_id
            context.user_data["order_supplier_name"] = supplier[2]
            context.user_data["supplier_has_delivery"] = supplier[6]

            msg = f"📦 *Products from {supplier[2]}:*\n\n"
            for p in products:
                stock_status = "✅ In Stock" if p[5] > 0 else "❌ Out of Stock"
                msg += f"*ID {p[0]}* — {p[1]}\n"
                if p[2]:
                    msg += f"   📝 {p[2]}\n"
                msg += f"   💵 ${p[3]}/{p[4]}\n"
                msg += f"   📦 Stock: {p[5]} {p[4]} {stock_status}\n\n"

            msg += "Enter the Product ID number (e.g. type *1*):"
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

            if product[6] <= 0:
                await update.message.reply_text(
                    f"❌ *{product[2]} is out of stock!*\n\nPlease choose another product.",
                    parse_mode="Markdown"
                )
                return ORDER_PRODUCT

            context.user_data["order_product_id"] = product_id
            context.user_data["order_material"] = product[2]
            context.user_data["order_price"] = product[4]
            context.user_data["order_unit"] = product[5]

            await update.message.reply_text(
                f"🧱 *{product[2]}* — ${product[4]}/{product[5]}\n"
                f"📦 Available stock: {product[6]} {product[5]}\n\n"
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

            current_stock = self.db.get_stock(d["order_product_id"])
            if qty > current_stock:
                await update.message.reply_text(
                    f"❌ *Insufficient Stock!*\n\n"
                    f"You requested: {qty} {d['order_unit']}\n"
                    f"Available: {current_stock} {d['order_unit']}\n\n"
                    f"Please enter {current_stock} or less.",
                    parse_mode="Markdown"
                )
                return ORDER_QUANTITY

            context.user_data["order_qty"] = qty

            if d.get("supplier_has_delivery"):
                keyboard = [["🚚 Delivery", "🏪 Pick Up"]]
                await update.message.reply_text(
                    "How would you like to receive your order?",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return ORDER_DELIVERY
            else:
                return await self._place_order(update, context, "pickup")

        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return ORDER_QUANTITY

    async def order_delivery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        delivery_type = "delivery" if "Delivery" in update.message.text else "pickup"
        return await self._place_order(update, context, delivery_type)

    async def _place_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE, delivery_type: str):
        d = context.user_data
        qty = d["order_qty"]
        buyer_name = self.db.get_buyer_name(update.effective_user.id)

        commission, total_cost = self.db.add_order(
            update.effective_user.id, buyer_name,
            d["order_supplier_id"], d["order_supplier_name"],
            d["order_product_id"], d["order_material"],
            qty, d["order_price"], delivery_type
        )

        delivery_text = "🚚 Delivery" if delivery_type == "delivery" else "🏪 Pick Up"

        await update.message.reply_text(
            f"✅ *Order Placed Successfully!*\n\n"
            f"🏢 Supplier: {d['order_supplier_name']}\n"
            f"🧱 Material: {d['order_material']}\n"
            f"📦 Quantity: {qty} {d['order_unit']}\n"
            f"💵 Price/unit: ${d['order_price']}\n"
            f"💰 Total Cost: ${total_cost}\n"
            f"📊 Platform Fee (2%): ${commission}\n"
            f"{delivery_text}\n"
            f"📋 Status: Pending\n\n"
            f"⏳ Waiting for supplier confirmation...",
            parse_mode="Markdown",
            reply_markup=BUYER_MENU
        )
        return ROLE_CHOICE

    # ── My Orders ────────────────────────────────────────────────────────
    async def my_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        orders = self.db.get_buyer_orders(update.effective_user.id)

        if not orders:
            await update.message.reply_text("You have no orders yet!", reply_markup=BUYER_MENU)
            return ROLE_CHOICE

        msg = "📋 *Your Orders:*\n\n"
        for o in orders:
            status_icon = "✅" if o[7] == "Confirmed" else "❌" if o[7] == "Rejected" else "⏳"
            delivery_icon = "🚚" if o[8] == "delivery" else "🏪"
            msg += (
                f"🔹 Order #{o[0]}\n"
                f"   🏢 {o[1]}\n"
                f"   🧱 {o[2]} | 📦 {o[3]} units\n"
                f"   💰 ${o[5]}\n"
                f"   {status_icon} {o[7]} | {delivery_icon} {o[9]}\n"
                f"   🕐 {o[10][:10]}\n\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=BUYER_MENU)
        return ROLE_CHOICE

    # ── AI Recommend ─────────────────────────────────────────────────────
    async def ai_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *AI Supplier Recommender*\n\nWhat material do you need?\n(e.g. Cement, Steel, Bricks)",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return AI_MATERIAL

    async def ai_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["ai_material"] = update.message.text
        await update.message.reply_text(
            "📍 Share your location so I can find the closest supplier!\n\nTap 📎 → Location",
            reply_markup=ReplyKeyboardRemove()
        )
        return AI_LOCATION

    async def ai_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.location:
            await update.message.reply_text("⚠️ Please share your location using 📎 → Location")
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
                f"❌ No suppliers found for *{material}* with available stock.",
                parse_mode="Markdown",
                reply_markup=BUYER_MENU
            )
            return ROLE_CHOICE

        supplier = self.db.get_supplier_by_id(best[0])
        products = self.db.get_supplier_products(best[0])
        delivery_text = "🚚 Delivery available" if supplier and supplier[6] else "🏪 Pickup only"

        products_msg = ""
        for p in products:
            if material.lower() in p[1].lower() and p[5] > 0:
                products_msg += f"   • {p[1]} — ${p[3]}/{p[4]} | 📦 {p[5]} {p[4]} in stock\n"

        await update.message.reply_text(
            f"🤖 *Best Supplier for {material}:*\n\n"
            f"🏆 *{best[2]}*\n"
            f"👤 {best[1]}\n"
            f"📞 {best[3]}\n"
            f"{delivery_text}\n\n"
            f"📦 *Matching Products:*\n{products_msg}\n"
            f"📌 *Why recommended:*\n{reason}",
            parse_mode="Markdown",
            reply_markup=BUYER_MENU
        )
        return ROLE_CHOICE