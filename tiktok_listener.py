from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent
import httpx

TIKTOK_USER = "dani._9_8_7"
MAIN_API = "http://localhost:5000/event"

client = TikTokLiveClient(unique_id=TIKTOK_USER)

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    username = event.user.nickname
    unique_id = event.user.unique_id

    gift_name = event.gift.name          # 👈 FIX
    amount = event.repeat_count or 1

    print(f"🎁 {username} (@{unique_id}) envió {gift_name} x{amount}")

    async with httpx.AsyncClient() as http:
        await http.post(MAIN_API, json={
            "user": username,
            "user_id": unique_id,
            "gift": gift_name,
            "amount": amount
        })

if __name__ == "__main__":
    print("🎥 TikTok listener iniciado")
    client.run()
