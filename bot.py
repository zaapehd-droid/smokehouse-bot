"""
SmokeHouse – Bot Telegram vendeur
Reçoit les commandes de la Mini App et les affiche au vendeur.

Installation :
  pip install python-telegram-bot==20.*

Usage :
  python bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ─── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8829252461:AAHuG4QJ17LmLqjaFaJoEvy0mL0FeHfjB_Y"
WEBAPP_URL = "https://accessoires-five.vercel.app"
SELLER_CHAT_ID = None                      # rempli automatiquement au /start
# ─────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

seller_chat_id = SELLER_CHAT_ID


# ── /start ───────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global seller_chat_id
    seller_chat_id = update.effective_chat.id

    kb = [[InlineKeyboardButton(
        "🛒  Ouvrir la boutique",
        web_app={"url": WEBAPP_URL}
    )]]
    await update.message.reply_text(
        "👋 *Bienvenue sur SmokeHouse !*\n\n"
        "Appuie sur le bouton ci-dessous pour ouvrir la boutique "
        "et passer ta commande directement dans Telegram.\n\n"
        "_Plateaux · Bols · Grinders — livraison rapide_ 🌿",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ── Réception d'une commande depuis la Mini App ──────────
async def receive_order(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    order_text = update.web_app_data.data
    buyer = update.effective_user

    buyer_name = buyer.full_name or "Inconnu"
    buyer_username = f"@{buyer.username}" if buyer.username else "(pas de @)"
    buyer_id = buyer.id

    # Confirmation à l'acheteur
    await update.message.reply_text(
        "✅ *Commande reçue !*\n\n"
        "Le vendeur va confirmer ta commande très vite.\n"
        "Tu seras contacté directement ici sur Telegram.",
        parse_mode="Markdown"
    )

    # Notification complète au vendeur
    notif = (
        f"🔔 *Nouvelle commande*\n"
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
        logging.warning("seller_chat_id non défini — fais /start d'abord.")


# ── Boutons Confirmer / Annuler ──────────────────────────
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


# ── /aide ────────────────────────────────────────────────
async def aide(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Commandes disponibles :*\n\n"
        "/start — Ouvrir la boutique\n"
        "/aide — Afficher cette aide\n\n"
        "Pour toute question : contacte le vendeur directement.",
        parse_mode="Markdown"
    )


# ── Main ─────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aide",  aide))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, receive_order))
    app.add_handler(CallbackQueryHandler(button_handler))
    logging.info("Bot démarré ✅")
    app.run_polling()


if __name__ == "__main__":
    main()
