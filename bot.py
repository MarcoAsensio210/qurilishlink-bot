from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler
)

from database import Database
from ai import AIRecommender
from handlers.start_handler import (
    StartHandler,
    ROLE_CHOICE,
    SUP_NAME, SUP_COMPANY, SUP_CONTACT, SUP_LOCATION, SUP_DELIVERY,
    SUP_PRODUCT_MATERIAL, SUP_PRODUCT_DESC, SUP_PRODUCT_PRICE, SUP_PRODUCT_UNIT, SUP_PRODUCT_STOCK, SUP_MORE_PRODUCTS,
    SUP_SELECT_PRODUCT, SUP_UPDATE_STOCK,
    SUP_SELECT_ORDER, SUP_UPDATE_DELIVERY,
    BUY_NAME, BUY_COMPANY,
    ORDER_SUPPLIER, ORDER_PRODUCT, ORDER_QUANTITY, ORDER_DELIVERY,
    AI_MATERIAL, AI_LOCATION,
    ADMIN_ACTION
)
from handlers.supplier_handler import SupplierHandler
from handlers.buyer_handler import BuyerHandler
from handlers.admin_handler import AdminHandler

TOKEN = "8753251383:AAH4Dl6WXRkKPD1_mfa3gRmUJUK79TSQTLs"


def main():
    db = Database()
    ai = AIRecommender(db)

    start_h = StartHandler(db)
    supplier_h = SupplierHandler(db)
    buyer_h = BuyerHandler(db)
    buyer_h.set_ai(ai)
    admin_h = AdminHandler(db)

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_h.start),
        ],
        states={
            ROLE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, start_h.role_choice),
            ],

            # Supplier registration
            SUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_name)],
            SUP_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_company)],
            SUP_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_contact)],
            SUP_LOCATION: [MessageHandler(filters.LOCATION, supplier_h.sup_location)],
            SUP_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_delivery)],

            # Supplier products
            SUP_PRODUCT_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_product_material)],
            SUP_PRODUCT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_product_desc)],
            SUP_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_product_price)],
            SUP_PRODUCT_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_product_unit)],
            SUP_PRODUCT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_product_stock)],
            SUP_MORE_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_more_products)],

            # Supplier stock update
            SUP_SELECT_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_select_product)],
            SUP_UPDATE_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_update_stock)],

            # Supplier delivery update
            SUP_SELECT_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_select_order)],
            SUP_UPDATE_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, supplier_h.sup_update_delivery)],

            # Buyer registration
            BUY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.buy_name)],
            BUY_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.buy_company)],

            # Order flow
            ORDER_SUPPLIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.order_supplier)],
            ORDER_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.order_product)],
            ORDER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.order_quantity)],
            ORDER_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.order_delivery)],

            # AI recommendation
            AI_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_h.ai_material)],
            AI_LOCATION: [MessageHandler(filters.LOCATION, buyer_h.ai_location)],

            # Admin
            ADMIN_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_h.handle),
            ],
        },
        fallbacks=[CommandHandler("start", start_h.start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(supplier_h.handle_callback))

    print("🚀 QurilishLink bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()