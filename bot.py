from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler
)

from handlers import BotHandlers

(
    ROLE,
    SUP_NAME, SUP_COMPANY, SUP_MATERIAL, SUP_PRICE, SUP_CONTACT, SUP_LOCATION,
    BUY_NAME, BUY_COMPANY,
    ORDER_SUPPLIER, ORDER_MATERIAL, ORDER_QUANTITY,
    ADMIN_ACTION, AI_MATERIAL, AI_LOCATION
) = range(15)

TOKEN = "8753251383:AAH4Dl6WXRkKPD1_mfa3gRmUJUK79TSQTLs"


def main():
    app = Application.builder().token(TOKEN).build()

    main_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", BotHandlers.start),
        ],
        states={
            ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.role_choice)],
            SUP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.sup_name)],
            SUP_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.sup_company)],
            SUP_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.sup_material)],
            SUP_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.sup_price)],
            SUP_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.sup_contact)],
            SUP_LOCATION: [MessageHandler(filters.LOCATION, BotHandlers.sup_location), 
                           MessageHandler(filters.ALL, BotHandlers.sup_location)],
            BUY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.buy_name)],
            BUY_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.buy_company)],
            ORDER_SUPPLIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.order_supplier)],
            ORDER_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.order_material)],
            ORDER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.order_quantity)],
            AI_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.ai_recommend_start)],
            AI_LOCATION: [MessageHandler(filters.LOCATION, BotHandlers.ai_recommend_location),
                          MessageHandler(filters.ALL, BotHandlers.ai_recommend_location)],
        },
        fallbacks=[CommandHandler("start", BotHandlers.start)],
    )

    app.add_handler(main_handler)
    
    print("🚀 QurilishLink bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()