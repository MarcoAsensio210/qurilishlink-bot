from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start_handler import (
    ROLE_CHOICE, SUP_NAME, SUP_COMPANY, SUP_CONTACT, SUP_LOCATION,
    SUP_PRODUCT_MATERIAL, SUP_PRODUCT_PRICE, SUP_PRODUCT_UNIT, SUP_MORE_PRODUCTS,
    SUPPLIER_MENU
)


class SupplierHandler:
    def __init__(self, database):
        self.db = database

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == "📦 My Products":
            return await self.my_products(update, context)
        elif text == "➕ Add Product":
            return await self.add_product_start(update, context)
        elif text == "📋 My Orders Received":
            return await self.my_orders_received(update, context)
        elif text == "📊 My Stats":
            return await self.my_stats(update, context)
        elif text == "🏠 Main Menu":
            await update.message.reply_text(
                "Main menu:",
                reply_markup=SUPPLIER_MENU
            )
            return ROLE_CHOICE
        else:
            await update.message.reply_text(
                "Please choose an option from the menu.",
                reply_markup=SUPPLIER_MENU
            )
            return ROLE_CHOICE

    # ── Registration ─────────────────────────────────────────────────────
    async def sup_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_name"] = update.message.text
        await update.message.reply_text("What is your company name?")
        return SUP_COMPANY

    async def sup_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_company"] = update.message.text
        await update.message.reply_text("What is your contact number or email?")
        return SUP_CONTACT

    async def sup_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["sup_contact"] = update.message.text
        await update.message.reply_text(
            "📍 Please share your business location!\n\n"
            "Tap the 📎 paperclip → Location → Send your location",
            reply_markup=ReplyKeyboardRemove()
        )
        return SUP_LOCATION

    async def sup_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.location:
            await update.message.reply_text(
                "⚠️ Please share your location using 📎 → Location"
            )
            return SUP_LOCATION

        d = context.user_data
        lat = update.message.location.latitude
        lon = update.message.location.longitude

        # Save supplier
        self.db.add_supplier(
            update.effective_user.id,
            d["sup_name"], d["sup_company"],
            d["sup_contact"], lat, lon
        )

        # Save user role
        self.db.register_user(
            update.effective_user.id,
            d["sup_name"], d["sup_company"], "supplier"
        )

        await update.message.reply_text(
            f"✅ *Supplier Registered!*\n\n"
            f"👤 Name: {d['sup_name']}\n"
            f"🏢 Company: {d['sup_company']}\n"
            f"📞 Contact: {d['sup_contact']}\n"
            f"📍 Location: Saved ✅\n\n"
            f"Now let's add your first product!\n\n"
            f"What material do you supply? (e.g. Cement, Steel, Bricks)",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return SUP_PRODUCT_MATERIAL

    async def sup_product_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["product_material"] = update.message.text
        await update.message.reply_text(
            f"What is your price per unit for *{update.message.text}* (in USD)?",
            parse_mode="Markdown"
        )
        return SUP_PRODUCT_PRICE

    async def sup_product_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            price = float(update.message.text)
            context.user_data["product_price"] = price
            await update.message.reply_text(
                "What is the unit of measurement?\n(e.g. kg, ton, m², piece, bag)"
            )
            return SUP_PRODUCT_UNIT
        except ValueError:
            await update.message.reply_text("Please enter a valid number (e.g. 25.50)")
            return SUP_PRODUCT_PRICE

    async def sup_product_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        d = context.user_data
        unit = update.message.text

        supplier = self.db.get_supplier_by_telegram_id(update.effective_user.id)
        if supplier:
            self.db.add_product(supplier[0], d["product_material"], d["product_price"], unit)

        keyboard = [["➕ Add Another Product", "✅ Done"]]
        await update.message.reply_text(
            f"✅ *Product Added!*\n\n"
            f"🧱 Material: {d['product_material']}\n"
            f"💵 Price: ${d['product_price']}/{unit}\n\n"
            f"Would you like to add another product?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SUP_MORE_PRODUCTS

    async def sup_more_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == "➕ Add Another Product":
            await update.message.reply_text(
                "What material do you supply?",
                reply_markup=ReplyKeyboardRemove()
            )
            return SUP_PRODUCT_MATERIAL

        else:
            supplier = self.db.get_supplier_by_telegram_id(update.effective_user.id)
            products = self.db.get_supplier_products(supplier[0]) if supplier else []

            msg = "🎉 *Registration Complete!*\n\n📦 *Your Products:*\n\n"
            for p in products:
                msg += f"• {p[1]} — ${p[2]}/{p[3]}\n"

            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                reply_markup=SUPPLIER_MENU
            )
            return ROLE_CHOICE

    # ── My Products ──────────────────────────────────────────────────────
    async def my_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        supplier = self.db.get_supplier_by_telegram_id(update.effective_user.id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        products = self.db.get_supplier_products(supplier[0])
        if not products:
            await update.message.reply_text(
                "You have no products yet. Tap ➕ Add Product to add one!",
                reply_markup=SUPPLIER_MENU
            )
            return ROLE_CHOICE

        msg = "📦 *Your Products:*\n\n"
        for p in products:
            msg += f"🔹 *ID {p[0]}* — {p[1]}\n"
            msg += f"   💵 ${p[2]}/{p[3]}\n\n"

        msg += "\nTo remove a product, type: /remove_product [ID]"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=SUPPLIER_MENU)
        return ROLE_CHOICE

    # ── Add Product ──────────────────────────────────────────────────────
    async def add_product_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "What material do you want to add?\n(e.g. Cement, Steel, Bricks, Sand)",
            reply_markup=ReplyKeyboardRemove()
        )
        return SUP_PRODUCT_MATERIAL

    # ── My Orders Received ───────────────────────────────────────────────
    async def my_orders_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        supplier = self.db.get_supplier_by_telegram_id(update.effective_user.id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        all_orders = self.db.get_all_orders()
        my_orders = [o for o in all_orders if o[2] == supplier[2]]

        if not my_orders:
            await update.message.reply_text(
                "No orders received yet.",
                reply_markup=SUPPLIER_MENU
            )
            return ROLE_CHOICE

        msg = "📋 *Orders Received:*\n\n"
        for o in my_orders:
            msg += (
                f"🔹 Order #{o[0]}\n"
                f"   👤 Buyer: {o[1]}\n"
                f"   🧱 Material: {o[3]}\n"
                f"   📦 Quantity: {o[4]} units\n"
                f"   💰 Total: ${o[5]}\n"
                f"   📊 Status: {o[7]}\n"
                f"   🕐 {o[8]}\n\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=SUPPLIER_MENU)
        return ROLE_CHOICE

    # ── My Stats ─────────────────────────────────────────────────────────
    async def my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        supplier = self.db.get_supplier_by_telegram_id(update.effective_user.id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        products = self.db.get_supplier_products(supplier[0])
        all_orders = self.db.get_all_orders()
        my_orders = [o for o in all_orders if o[2] == supplier[2]]
        total_revenue = sum(o[5] for o in my_orders)

        await update.message.reply_text(
            f"📊 *Your Statistics:*\n\n"
            f"🏢 Company: {supplier[2]}\n"
            f"📦 Products listed: {len(products)}\n"
            f"📋 Total orders received: {len(my_orders)}\n"
            f"💰 Total sales value: ${total_revenue:.2f}\n",
            parse_mode="Markdown",
            reply_markup=SUPPLIER_MENU
        )
        return ROLE_CHOICE