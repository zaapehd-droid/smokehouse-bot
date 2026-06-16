"""
SmokeHouse – Bot Telegram vendeur
Utilise httpx directement, sans python-telegram-bot
"""

import asyncio
import httpx
import json
import logging
import os

BOT_TOKEN = "8829252461:AAHuG4QJ17LmLqjaFaJoEvy0mL0FeHfjB_Y"
WEBAPP_URL = "https://accessoires-five.vercel.app"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
DATA_FILE = "/app/seller.json"

logging.basicConfig(format="%(asctime)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


def load_seller():
    try:
        with open(DATA_FILE) as f:
            return json.load(f).get("chat_id")
    except:
        return None


def save_seller(chat_id):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"chat_id": chat_id}, f)
    except:
        pass


seller_chat_id = load_seller()


async def call(client, method, **params):
    r = await client.post(f"{API}/{method}", json=params)
    return r.json()


async def send(client, chat_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        params["reply_markup"] = reply_markup
    return await call(client, "sendMessage", **params)


async def handle_update(client, update):
    global seller_chat_id

    msg = update.get("message") or update.get("edited_message")
    if msg:
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        user = msg.get("from", {})

        # Commande reçue depuis la Mini App
        web_data = msg.get("web_app_data")
        if web_data:
            order_text = web_data["data"]
            buyer_name = (user.get("first_name", "") + " " + user.get("last_name", "")).strip()
            buyer_user = f"@{user['username']}" if user.get("username") else "(pas de @)"
            buyer_id = user["id"]

            # Confirmation à l'acheteur
            await send(client, chat_id,
                "✅ *Commande reçue !*\n\n"
                "Le vendeur va confirmer très vite.\n"
                "Tu seras contacté ici sur Telegram.")

            # Notification au vendeur
            seller = seller_chat_id or load_seller()
            if seller:
                notif = (
                    f"🔔 *Nouvelle commande SmokeHouse*\n"
                    f"──────────────────\n"
                    f"{order_text}\n"
                    f"──────────────────\n"
                    f"👤 *Acheteur :* {buyer_name} ({buyer_user})\n"
                    f"🆔 `{buyer_id}`"
                )
                kb = {"inline_keyboard": [[
                    {"text": "✅ Confirmer", "callback_data": f"confirm:{buyer_id}"},
                    {"text": "❌ Annuler",   "callback_data": f"cancel:{buyer_id}"}
                ]]}
                await send(client, seller, notif, reply_markup=kb)
                log.info(f"Commande envoyée au vendeur {seller}")
            else:
                log.warning("Vendeur inconnu — fais /start d'abord !")
            return

        if text == "/start":
            seller_chat_id = chat_id
            save_seller(chat_id)
            log.info(f"Vendeur enregistré : {chat_id}")
            kb = {"inline_keyboard": [[
                {"text": "🛒  Ouvrir la boutique", "web_app": {"url": WEBAPP_URL}}
            ]]}
            await send(client, chat_id,
                "👋 *Bienvenue sur SmokeHouse !*\n\n"
                "Appuie sur le bouton pour ouvrir la boutique.\n\n"
                "_Plateaux · Bols · Grinders_ 🌿",
                reply_markup=kb)

        elif text == "/aide":
            await send(client, chat_id,
                "*Commandes :*\n/start — Ouvrir la boutique\n/aide — Cette aide")

    # Boutons confirmer/annuler
    cb = update.get("callback_query")
    if cb:
        query_id = cb["id"]
        data = cb.get("data", "")
        msg_id = cb["message"]["message_id"]
        chat_id = cb["message"]["chat"]["id"]

        await call(client, "answerCallbackQuery", callback_query_id=query_id)

        if ":" in data:
            action, buyer_id = data.split(":")
            buyer_id = int(buyer_id)

            if action == "confirm":
                await send(client, buyer_id,
                    "🎉 *Ta commande est confirmée !*\n\n"
                    "On prépare ton colis, tu recevras les infos de livraison. Merci ! 🙏")
                await call(client, "editMessageReplyMarkup",
                    chat_id=chat_id, message_id=msg_id, reply_markup={"inline_keyboard": []})
                await send(client, chat_id, "✅ Client notifié — commande confirmée.")

            elif action == "cancel":
                await send(client, buyer_id,
                    "😔 *Ta commande a été annulée.*\n\n"
                    "Contacte le vendeur pour plus d'infos.")
                await call(client, "editMessageReplyMarkup",
                    chat_id=chat_id, message_id=msg_id, reply_markup={"inline_keyboard": []})
                await send(client, chat_id, "❌ Client notifié — commande annulée.")


async def main():
    offset = 0
    log.info("Bot SmokeHouse démarré ✅")
    log.info(f"Vendeur chargé depuis fichier : {seller_chat_id}")
    async with httpx.AsyncClient(timeout=60) as client:
        while True:
            try:
                resp = await call(client, "getUpdates",
                    offset=offset, timeout=30, allowed_updates=["message", "callback_query"])
                for update in resp.get("result", []):
                    offset = update["update_id"] + 1
                    await handle_update(client, update)
            except Exception as e:
                log.error(f"Erreur : {e}")
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
