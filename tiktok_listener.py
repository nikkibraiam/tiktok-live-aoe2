from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent
import httpx
import asyncio
import time

TIKTOK_USER = "dani._9_8_7"
MAIN_API = "http://localhost:5000/event"
DEBOUNCE_SECONDS = 0.5

client = TikTokLiveClient(unique_id=TIKTOK_USER)

# ======================
# BUFFER
# key = (user_id, gift)
# ======================
gift_buffer = {}

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    user = event.user.nickname
    user_id = event.user.unique_id
    gift = event.gift.name
    count = event.repeat_count or 1

    key = (user_id, gift)

    now = time.time()
    gift_buffer[key] = {
        "user": user,
        "user_id": user_id,
        "gift": gift,
        "count": count,
        "last_update": now
    }

    print(f"🎁 BUFFER {user} → {gift} x{count}")

async def debounce_loop():
    while True:
        now = time.time()
        to_send = []

        for key, data in list(gift_buffer.items()):
            if now - data["last_update"] >= DEBOUNCE_SECONDS:
                to_send.append((key, data))

        for key, data in to_send:
            print(f"🚀 SEND {data['user']} → {data['gift']} x{data['count']}")

            async with httpx.AsyncClient() as http:
                await http.post(MAIN_API, json={
                    "user": data["user"],
                    "user_id": data["user_id"],
                    "gift": data["gift"],
                    "amount": data["count"]
                })

            del gift_buffer[key]

        await asyncio.sleep(0.1)

if __name__ == "__main__":
    print("🎥 TikTok listener iniciado")
    asyncio.create_task(debounce_loop())
    client.run()
