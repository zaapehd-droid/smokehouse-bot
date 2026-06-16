"""
SmokeHouse – Bot Telegram vendeur
Compatible python-telegram-bot 21.x / Python 3.13
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = "8829252461:AAHuG4QJ17LmLqjaFaJoEvy0mL0FeHfjB_Y"
WEBAPP_URL = "https://accessoires-five.vercel.app"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

seller_chat_id = None


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global seller_chat_id
    seller_chat_id = update.effective_chat.id

    kb = [[InlineKeyboardButton(
        "🛒  Ouvrir la boutique",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    await update.message.reply_text(
        "👋 *Bienvenue sur SmokeHouse !*\n\n"
        "Appuie sur le bouton ci-dessous pour ouvrir la boutique "
        "et passer ta commande directement dans Telegram.\n\n"
        "_Plateaux · Bols · Grinders — livraison rapide_ 🌿",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def receive_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order_text = update.effective_message.web_app_data.data
    buyer = update.effective_user

    buyer_name = buyer.full_name or "Inconnu"
    buyer_username = f"@{buyer.username}" if buyer.username else "(pas de @)"
    buyer_id = buyer.id

    await update.effective_message.reply_text(
        "✅ *Commande reçue !*\n\n"
        "Le vendeur va confirmer ta commande très vite.\n"
        "Tu seras contacté directement ici sur Telegram.",
        parse_mode="Markdown"
    )

    notif = (
        f"🔔 *Nouvelle commande SmokeHouse*\n"
        f"──────────────────\n"
        f"{order_text}\n"
        f"──────────────────\n"
        f"👤 *Acheteur :* {buyer_name} ({buyer_username})\n"
        f"🆔 `{buyer_id}`"
    )

    kb = [[
        InlineKeyboardButton("✅ Confirmer", callback_data=f"confirm:{buyer_id}"),
        InlineKeyboardButton("❌ Annuler",   callback_data=f"cancel:{buyer_id}"),
    ]]

    if seller_chat_id:
        await ctx.bot.send_message(
            chat_id=seller_chat_id,
            text=notif,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        logging.warning("seller_chat_id non défini — envoie /start d'abord.")


async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, buyer_id = query.data.split(":")
    buyer_id = int(buyer_id)

    if action == "confirm":
        await ctx.bot.send_message(
            chat_id=buyer_id,
            text="🎉 *Ta commande est confirmée !*\n\n"
                 "On prépare ton colis. Tu recevras les infos de livraison prochainement. Merci ! 🙏",
            parse_mode="Markdown"
        )
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Commande confirmée et client notifié.")

    elif action == "cancel":
        await ctx.bot.send_message(
            chat_id=buyer_id,
            text="😔 *Ta commande a été annulée.*\n\n"
                 "Un article est peut-être en rupture de stock. "
                 "Contacte le vendeur pour plus d'infos.",
            parse_mode="Markdown"
        )
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("❌ Commande annulée et client notifié.")


async def aide(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Commandes disponibles :*\n\n"
        "/start — Ouvrir la boutique\n"
        "/aide — Afficher cette aide\n\n"
        "Pour toute question : contacte le vendeur directement.",
        parse_mode="Markdown"
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aide",  aide))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, receive_order))
    app.add_handler(CallbackQueryHandler(button_handler))
    logging.info("Bot démarré ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
