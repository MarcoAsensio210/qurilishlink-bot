from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start_handler import (
    ROLE_CHOICE, SUP_NAME, SUP_COMPANY, SUP_CONTACT, SUP_LOCATION, SUP_DELIVERY,
    SUP_PRODUCT_MATERIAL, SUP_PRODUCT_DESC, SUP_PRODUCT_PRICE, SUP_PRODUCT_UNIT, SUP_PRODUCT_STOCK, SUP_MORE_PRODUCTS,
    SUP_SELECT_PRODUCT, SUP_UPDATE_STOCK,
    SUP_SELECT_ORDER, SUP_UPDATE_DELIVERY,
    SUPPLIER_MENU, get_supplier_menu
)

SUPPLIER_MINIAPP_URL = "https://marcoasensio210.github.io/qurilishlink-bot/miniapp/supplier.html"


class SupplierHandler:
    def __init__(self, database):
        self.db = database

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        telegram_id = update.effective_user.id

        if text == "📦 My Products":
            return await self.my_products(update, context)
        elif text == "➕ Add Product":
            return await self.add_product_start(update, context)
        elif text == "📋 My Orders Received":
            return await self.my_orders_received(update, context)
        elif text == "📊 My Stats":
            return await self.my_stats(update, context)
        elif text == "📊 Update Stock":
            return await self.update_stock_start(update, context)
        elif text == "🚚 Update Delivery":
            return await self.update_delivery_start(update, context)
        elif text == "🌐 My Dashboard":
            return await self.open_dashboard(update, context)
        elif text == "🏠 Main Menu":
            await update.message.reply_text(
                "Main menu:",
                reply_markup=get_supplier_menu(telegram_id)
            )
            return ROLE_CHOICE
        else:
            await update.message.reply_text(
                "Please choose an option from the menu.",
                reply_markup=get_supplier_menu(telegram_id)
            )
            return ROLE_CHOICE

    # ── Mini App ─────────────────────────────────────────────────────────
    async def open_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🌐 Open Supplier Dashboard",
                web_app=WebAppInfo(url=SUPPLIER_MINIAPP_URL)
            )
        ]])
        await update.message.reply_text(
            "📊 Open your Supplier Dashboard:",
            reply_markup=keyboard
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
            await update.message.reply_text("⚠️ Please share your location using 📎 → Location")
            return SUP_LOCATION

        context.user_data["sup_lat"] = update.message.location.latitude
        context.user_data["sup_lon"] = update.message.location.longitude

        keyboard = [["🚚 Yes, I offer delivery", "🏪 No, pickup only"]]
        await update.message.reply_text(
            "🚚 Do you offer delivery to buyers?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SUP_DELIVERY

    async def sup_delivery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        has_delivery = 1 if "Yes" in text else 0
        context.user_data["has_delivery"] = has_delivery
        d = context.user_data

        self.db.add_supplier(
            update.effective_user.id,
            d["sup_name"], d["sup_company"],
            d["sup_contact"], d["sup_lat"], d["sup_lon"],
            has_delivery
        )
        self.db.register_user(
            update.effective_user.id,
            d["sup_name"], d["sup_company"], "supplier"
        )

        delivery_text = "🚚 Delivery available" if has_delivery else "🏪 Pickup only"
        await update.message.reply_text(
            f"✅ *Supplier Registered!*\n\n"
            f"👤 Name: {d['sup_name']}\n"
            f"🏢 Company: {d['sup_company']}\n"
            f"📞 Contact: {d['sup_contact']}\n"
            f"📍 Location: Saved ✅\n"
            f"🚚 Delivery: {delivery_text}\n\n"
            f"Now let's add your first product!\n\n"
            f"What material do you supply? (e.g. Cement, Steel, Bricks)",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return SUP_PRODUCT_MATERIAL

    # ── Product Registration ──────────────────────────────────────────────
    async def sup_product_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["product_material"] = update.message.text
        await update.message.reply_text(
            f"Add a short description for *{update.message.text}*\n"
            f"(e.g. High quality Portland cement, Grade 42.5)",
            parse_mode="Markdown"
        )
        return SUP_PRODUCT_DESC

    async def sup_product_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["product_desc"] = update.message.text
        await update.message.reply_text(
            f"What is your price per unit for *{context.user_data['product_material']}* (in USD)?",
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
        context.user_data["product_unit"] = update.message.text
        await update.message.reply_text("How many units do you currently have in stock?\n(e.g. 10000)")
        return SUP_PRODUCT_STOCK

    async def sup_product_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            stock = int(update.message.text)
            d = context.user_data
            telegram_id = update.effective_user.id

            supplier = self.db.get_supplier_by_telegram_id(telegram_id)
            if supplier:
                self.db.add_product(
                    supplier[0],
                    d["product_material"],
                    d.get("product_desc", ""),
                    d["product_price"],
                    d["product_unit"],
                    stock
                )

            keyboard = [["➕ Add Another Product", "✅ Done"]]
            await update.message.reply_text(
                f"✅ *Product Added!*\n\n"
                f"🧱 Material: {d['product_material']}\n"
                f"📝 Description: {d.get('product_desc', 'N/A')}\n"
                f"💵 Price: ${d['product_price']}/{d['product_unit']}\n"
                f"📦 Stock: {stock} {d['product_unit']}\n\n"
                f"Would you like to add another product?",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return SUP_MORE_PRODUCTS
        except ValueError:
            await update.message.reply_text("Please enter a valid number (e.g. 10000)")
            return SUP_PRODUCT_STOCK

    async def sup_more_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        telegram_id = update.effective_user.id

        if text == "➕ Add Another Product":
            await update.message.reply_text(
                "What material do you want to add?",
                reply_markup=ReplyKeyboardRemove()
            )
            return SUP_PRODUCT_MATERIAL
        else:
            supplier = self.db.get_supplier_by_telegram_id(telegram_id)
            products = self.db.get_supplier_products(supplier[0]) if supplier else []

            msg = "🎉 *Registration Complete!*\n\n📦 *Your Products:*\n\n"
            for p in products:
                msg += f"• {p[1]} — ${p[3]}/{p[4]} | 📦 {p[5]} {p[4]}\n"

            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                reply_markup=get_supplier_menu(telegram_id)
            )
            return ROLE_CHOICE

    # ── My Products ──────────────────────────────────────────────────────
    async def my_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        supplier = self.db.get_supplier_by_telegram_id(telegram_id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        products = self.db.get_supplier_products(supplier[0])
        if not products:
            await update.message.reply_text(
                "You have no products yet. Tap ➕ Add Product to add one!",
                reply_markup=get_supplier_menu(telegram_id)
            )
            return ROLE_CHOICE

        msg = "📦 *Your Products:*\n\n"
        for p in products:
            stock_status = "✅ In Stock" if p[5] > 0 else "❌ Out of Stock"
            msg += f"🔹 *ID {p[0]}* — {p[1]}\n"
            msg += f"   📝 {p[2]}\n" if p[2] else ""
            msg += f"   💵 ${p[3]}/{p[4]}\n"
            msg += f"   📦 Stock: {p[5]} {p[4]} {stock_status}\n\n"

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_supplier_menu(telegram_id))
        return ROLE_CHOICE

    # ── Add Product ──────────────────────────────────────────────────────
    async def add_product_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "What material do you want to add?\n(e.g. Cement, Steel, Bricks, Sand)",
            reply_markup=ReplyKeyboardRemove()
        )
        return SUP_PRODUCT_MATERIAL

    # ── Update Stock ─────────────────────────────────────────────────────
    async def update_stock_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        supplier = self.db.get_supplier_by_telegram_id(telegram_id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        products = self.db.get_supplier_products(supplier[0])
        if not products:
            await update.message.reply_text("You have no products yet.", reply_markup=get_supplier_menu(telegram_id))
            return ROLE_CHOICE

        msg = "📊 *Select Product to Update Stock:*\n\n"
        for p in products:
            msg += f"*ID {p[0]}* — {p[1]}\n   Current stock: {p[5]} {p[4]}\n\n"
        msg += "Enter the *Product ID* to update:"

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        return SUP_SELECT_PRODUCT

    async def sup_select_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            product_id = int(update.message.text)
            product = self.db.get_product_by_id(product_id)
            if not product:
                await update.message.reply_text("Product not found. Please enter a valid ID.")
                return SUP_SELECT_PRODUCT

            context.user_data["update_product_id"] = product_id
            context.user_data["update_product_name"] = product[2]
            context.user_data["update_product_unit"] = product[5]
            current_stock = self.db.get_stock(product_id)

            await update.message.reply_text(
                f"📦 *{product[2]}*\nCurrent stock: *{current_stock} {product[5]}*\n\n"
                f"How many units do you want to ADD?\n(Use negative to reduce, e.g. -500)",
                parse_mode="Markdown"
            )
            return SUP_UPDATE_STOCK
        except ValueError:
            await update.message.reply_text("Please enter a valid Product ID number.")
            return SUP_SELECT_PRODUCT

    async def sup_update_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            quantity = int(update.message.text)
            d = context.user_data
            product_id = d["update_product_id"]
            telegram_id = update.effective_user.id
            current_stock = self.db.get_stock(product_id)
            new_stock = current_stock + quantity

            if new_stock < 0:
                await update.message.reply_text(
                    f"❌ Cannot reduce stock below 0!\nCurrent: {current_stock} {d['update_product_unit']}"
                )
                return SUP_UPDATE_STOCK

            self.db.update_stock(product_id, quantity)
            action = "added to" if quantity > 0 else "removed from"

            await update.message.reply_text(
                f"✅ *Stock Updated!*\n\n"
                f"🧱 {d['update_product_name']}\n"
                f"📦 {abs(quantity)} {d['update_product_unit']} {action} stock\n"
                f"✅ New stock: {new_stock} {d['update_product_unit']}",
                parse_mode="Markdown",
                reply_markup=get_supplier_menu(telegram_id)
            )
            return ROLE_CHOICE
        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return SUP_UPDATE_STOCK

    # ── Update Delivery ───────────────────────────────────────────────────
    async def update_delivery_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        supplier = self.db.get_supplier_by_telegram_id(telegram_id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        all_orders = self.db.get_all_orders()
        my_orders = [o for o in all_orders if o[2] == supplier[2] and o[7] == "Confirmed"]

        if not my_orders:
            await update.message.reply_text(
                "No confirmed orders to update.",
                reply_markup=get_supplier_menu(telegram_id)
            )
            return ROLE_CHOICE

        msg = "🚚 *Select Order to Update:*\n\n"
        for o in my_orders:
            delivery_icon = "🚚" if o[8] == "delivery" else "🏪"
            msg += f"*Order #{o[0]}* — {o[1]}\n"
            msg += f"   🧱 {o[3]} | {delivery_icon} {o[8]} | 📊 {o[9]}\n\n"

        msg += "Enter the *Order ID*:"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        return SUP_SELECT_ORDER

    async def sup_select_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            order_id = int(update.message.text)
            order = self.db.get_order_by_id(order_id)
            if not order:
                await update.message.reply_text("Order not found.")
                return SUP_SELECT_ORDER

            context.user_data["update_order_id"] = order_id
            delivery_type = order[11]

            if delivery_type == "delivery":
                keyboard = [["📦 Processing", "🚚 Out for Delivery"], ["✅ Delivered"]]
            else:
                keyboard = [["📦 Processing", "✅ Ready for Pickup"], ["✅ Picked Up"]]

            await update.message.reply_text(
                f"📋 *Order #{order_id}*\nCurrent status: {order[13]}\n\nSelect new status:",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return SUP_UPDATE_DELIVERY
        except ValueError:
            await update.message.reply_text("Please enter a valid Order ID.")
            return SUP_SELECT_ORDER

    async def sup_update_delivery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_status = update.message.text
        order_id = context.user_data.get("update_order_id")
        telegram_id = update.effective_user.id

        self.db.update_delivery_status(order_id, new_status)
        order = self.db.get_order_by_id(order_id)

        try:
            status_msg = {
                "📦 Processing": "Your order is being processed!",
                "🚚 Out for Delivery": "Your order is out for delivery! 🚚",
                "✅ Delivered": "Your order has been delivered! ✅",
                "✅ Ready for Pickup": "Your order is ready for pickup! 🏪",
                "✅ Picked Up": "Your pickup has been confirmed! ✅"
            }.get(new_status, f"Order status: {new_status}")

            await context.bot.send_message(
                chat_id=order[1],
                text=f"📦 *Order #{order_id} Update*\n\n{status_msg}\n\n"
                     f"🧱 Material: {order[6]}\n📦 Quantity: {order[7]} units",
                parse_mode="Markdown"
            )
        except:
            pass

        await update.message.reply_text(
            f"✅ *Delivery Status Updated!*\n\nOrder #{order_id}: {new_status}",
            parse_mode="Markdown",
            reply_markup=get_supplier_menu(telegram_id)
        )
        return ROLE_CHOICE

    # ── My Orders Received ───────────────────────────────────────────────
    async def my_orders_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        supplier = self.db.get_supplier_by_telegram_id(telegram_id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        all_orders = self.db.get_all_orders()
        my_orders = [o for o in all_orders if o[2] == supplier[2]]

        if not my_orders:
            await update.message.reply_text("No orders received yet.", reply_markup=get_supplier_menu(telegram_id))
            return ROLE_CHOICE

        await update.message.reply_text(
            f"📋 *Orders Received ({len(my_orders)} total):*",
            parse_mode="Markdown",
            reply_markup=get_supplier_menu(telegram_id)
        )

        for o in my_orders:
            delivery_icon = "🚚" if o[8] == "delivery" else "🏪"
            order_text = (
                f"🔹 *Order #{o[0]}*\n"
                f"   👤 Buyer: {o[1]}\n"
                f"   🧱 Material: {o[3]}\n"
                f"   📦 Quantity: {o[4]} units\n"
                f"   💰 Total: ${o[5]}\n"
                f"   {delivery_icon} Type: {o[8].capitalize()}\n"
                f"   📊 Status: {o[7]}\n"
                f"   🚚 Delivery: {o[9]}\n"
                f"   🕐 {o[10][:10]}"
            )

            if o[7] == "Pending":
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{o[0]}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{o[0]}")
                ]])
                await update.message.reply_text(order_text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await update.message.reply_text(order_text, parse_mode="Markdown")

        return ROLE_CHOICE

    # ── My Stats ─────────────────────────────────────────────────────────
    async def my_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        supplier = self.db.get_supplier_by_telegram_id(telegram_id)
        if not supplier:
            await update.message.reply_text("You are not registered as a supplier.")
            return ROLE_CHOICE

        products = self.db.get_supplier_products(supplier[0])
        all_orders = self.db.get_all_orders()
        my_orders = [o for o in all_orders if o[2] == supplier[2]]
        total_revenue = sum(o[5] for o in my_orders)
        confirmed = len([o for o in my_orders if o[7] == "Confirmed"])
        pending = len([o for o in my_orders if o[7] == "Pending"])
        delivery_status = "🚚 Available" if supplier[6] else "🏪 Pickup Only"

        msg = (
            f"📊 *Your Statistics:*\n\n"
            f"🏢 Company: {supplier[2]}\n"
            f"🚚 Delivery: {delivery_status}\n"
            f"📦 Products listed: {len(products)}\n\n"
            f"📋 *Stock Summary:*\n"
        )
        for p in products:
            stock_status = "✅" if p[5] > 0 else "❌"
            msg += f"   {stock_status} {p[1]}: {p[5]} {p[4]}\n"

        msg += (
            f"\n📦 Total orders: {len(my_orders)}\n"
            f"✅ Confirmed: {confirmed}\n"
            f"⏳ Pending: {pending}\n"
            f"💰 Total sales: ${total_revenue:.2f}\n"
        )

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_supplier_menu(telegram_id))
        return ROLE_CHOICE

    # ── Handle Callback ──────────────────────────────────────────────────
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data.startswith("confirm_"):
            order_id = int(data.split("_")[1])
            order = self.db.get_order_by_id(order_id)
            self.db.update_order_status(order_id, "Confirmed")
            if order[5]:
                self.db.reduce_stock(order[5], order[7])

            await query.edit_message_text(
                f"✅ *Order #{order_id} Confirmed!*\n\n"
                f"👤 Buyer: {order[2]}\n"
                f"🧱 Material: {order[6]}\n"
                f"📦 Quantity: {order[7]} units\n"
                f"💰 Total: ${order[9]}",
                parse_mode="Markdown"
            )
            try:
                delivery_type = order[11]
                delivery_msg = "🚚 Your order will be delivered!" if delivery_type == "delivery" else "🏪 Your order is ready for pickup!"
                await context.bot.send_message(
                    chat_id=order[1],
                    text=f"✅ *Your order #{order_id} has been CONFIRMED!*\n\n"
                         f"🏢 Supplier: {order[3]}\n"
                         f"🧱 Material: {order[6]}\n"
                         f"📦 Quantity: {order[7]} units\n"
                         f"💰 Total: ${order[9]}\n\n{delivery_msg}",
                    parse_mode="Markdown"
                )
            except:
                pass

        elif data.startswith("reject_"):
            order_id = int(data.split("_")[1])
            order = self.db.get_order_by_id(order_id)
            self.db.update_order_status(order_id, "Rejected")
            await query.edit_message_text(f"❌ *Order #{order_id} Rejected*", parse_mode="Markdown")
            try:
                await context.bot.send_message(
                    chat_id=order[1],
                    text=f"❌ *Your order #{order_id} has been REJECTED*\n\n"
                         f"🏢 Supplier: {order[3]}\n"
                         f"🧱 Material: {order[6]}\n\nPlease try another supplier.",
                    parse_mode="Markdown"
                )
            except:
                pass