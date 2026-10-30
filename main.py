import os
import random
import sqlite3
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

TOKEN = os.environ["VK_TOKEN"]
GROUP_ID = int(os.environ["VK_GROUP_ID"])

vk = vk_api.VkApi(token=TOKEN)
api = vk.get_api()
longpoll = VkBotLongPoll(vk, GROUP_ID)

db = sqlite3.connect("monarch.db")
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 100000
)
""")
db.commit()

def balance(user):
    db.execute(
        "INSERT OR IGNORE INTO users(user_id) VALUES(?)",
        (user,)
    )
    db.commit()
    return db.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user,)
    ).fetchone()[0]

def change(user, amount):
    balance(user)
    db.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, user)
    )
    db.commit()

def send(peer, message):
    api.messages.send(
        peer_id=peer,
        message=message,
        random_id=0
    )

for event in longpoll.listen():
    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "").lower().strip()
    user = msg["from_id"]
    peer = msg["peer_id"]

    if text == "/старт":
        balance(user)
        send(peer, "👑 МОНАРХ CASINO\nДобро пожаловать!\nТвой стартовый баланс: 100000 MRC")

    elif text == "/баланс":
        send(peer, f"💎 Твой баланс: {balance(user)} MRC")

    elif text.startswith("/слоты"):
        bet = 100
        if balance(user) < bet:
            send(peer, "Недостаточно MRC!")
            continue

        change(user, -bet)
        reels = [random.choice(["🍒", "🍋", "7️⃣", "💎"]) for _ in range(3)]
        win = bet * 5 if len(set(reels)) == 1 else 0
        change(user, win)

        send(peer, f"🎰 {' | '.join(reels)}\nВыигрыш: {win} MRC")

    elif text == "/кости":
        bet = 100
        if balance(user) < bet:
            send(peer, "Недостаточно MRC!")
            continue

        change(user, -bet)
        roll = random.randint(1, 6)
        win = bet * 2 if roll >= 4 else 0
        change(user, win)

        send(peer, f"🎲 Выпало: {roll}\nВыигрыш: {win} MRC")

    elif text == "/помощь":
        send(peer, "👑 МОНАРХ CASINO\n/старт\n/баланс\n/слоты\n/кости\n/помощь")
