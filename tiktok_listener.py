from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, GiftEvent, LikeEvent, FollowEvent, CommentEvent, ShareEvent
import httpx
import asyncio
import time

TIKTOK_USER = "alejandra_acevedo_"
MAIN_API = "http://localhost:5000/"
DEBOUNCE_SECONDS = 0.5

client = TikTokLiveClient(unique_id=TIKTOK_USER)

# ======================
# BUFFER
# key = (user_id, gift)
# ======================
gift_buffer = {}
like_buffer = {}

debounce_started = False

def avatar_url(user):
    for field in [
        "avatar_thumb",
        "avatar_medium",
        "avatar_large",
        "avatar_jpg",
        "profile_picture",
        "avatar"
    ]:
        img = getattr(user, field, None)
        if not img:
            continue

        # TikTokLive ImageModel variants
        if hasattr(img, "url") and isinstance(img.url, str):
            return img.url

        if hasattr(img, "urls") and img.urls:
            return img.urls[0]

        if hasattr(img, "url_list") and img.url_list:
            return img.url_list[0]

        if isinstance(img, str):
            return img

    return ""


@client.on(ConnectEvent)
async def on_connect(event):
    global debounce_started
    if not debounce_started:
        debounce_started = True
        print("✅ Conectado a TikTok Live – iniciando debounce")
        asyncio.create_task(debounce_loop())


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):

    # Ignorar eventos intermedios de streak
    is_streaking = getattr(event, "streaking", False)

    if event.gift.streakable and is_streaking:
        return

    print(vars(event.user))
    user = event.user.nickname
    user_id = event.user.unique_id
    gift = event.gift.name
    count = event.repeat_count or 1
    avatar = avatar_url(event.user)
    print("evento avatar: " + avatar)
    gift_value = event.gift.diamond_count

    key = (user_id, gift)
    now = time.time()

    if key not in gift_buffer:
        gift_buffer[key] = {
            "user": user,
            "user_id": user_id,
            "gift": gift,
            "count": 0,
            "avatar": avatar,
            "diamonds": gift_value,
            "last_update": now
        }

    gift_buffer[key]["count"] += count
    gift_buffer[key]["last_update"] = now

    print(f"🎁 GIFT {user} → {gift} (+{count}) = {gift_buffer[key]['count']}")



@client.on(LikeEvent)
async def on_like(event: LikeEvent):
    user_id = event.user.unique_id
    user = event.user.nickname
    count = event.count  # likes enviados en ese evento
    avatar = avatar_url(event.user)
    print("evento avatar: " + avatar)

    if user_id not in like_buffer:
        like_buffer[user_id] = {
            "user": user,
            "count": 0,
            "avatar": avatar,
            "last_update": time.time()
        }

    like_buffer[user_id]["count"] += count
    like_buffer[user_id]["last_update"] = time.time()

    print(f"❤️ LIKES {user} +{count} = {like_buffer[user_id]['count']}")

@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    print(f"➕ FOLLOW {event.user.nickname}")
    avatar = avatar_url(event.user)
    print("evento avatar: " + avatar)

    await httpx.AsyncClient().post(MAIN_API + "follow", json={
        "user": event.user.nickname,
        "user_id": event.user.unique_id,
        "avatar": avatar,
         "diamonds": 3
    })

@client.on(ShareEvent)
async def on_share(event: ShareEvent):
    print(f"🔁 SHARE {event.user.nickname}")

    avatar = avatar_url(event.user)
    print("evento avatar: " + avatar)

    await httpx.AsyncClient().post(MAIN_API + "share", json={
        "user": event.user.nickname,
        "user_id": event.user.unique_id,
        "avatar": avatar,
         "diamonds": 3
    })

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    print(f"💬 {event.user.nickname}: {event.comment}")
    avatar = avatar_url(event.user)
    print("evento avatar: " + avatar)

    await httpx.AsyncClient().post(MAIN_API + "comment", json={
        "user": event.user.nickname,
        "user_id": event.user.unique_id,
        "message": event.comment,
        "avatar": avatar,
         "diamonds": 1
    })


async def debounce_loop():
    async with httpx.AsyncClient() as http:
        while True:
            now = time.time()

            to_send_gifts = []
            for key, data in list(gift_buffer.items()):
                if now - data["last_update"] >= DEBOUNCE_SECONDS:
                    to_send_gifts.append((key, data))

            await process_gifts(http, to_send_gifts)

            to_send_likes = []
            for key, data in list(like_buffer.items()):
                if now - data["last_update"] >= DEBOUNCE_SECONDS:
                    to_send_likes.append((key, data))
            await process_likes(http, to_send_likes)

            await asyncio.sleep(0.1)

async def process_gifts(http, to_send):
    for key, data in to_send:
        await http.post(MAIN_API + "gift", json={
            "user": data["user"],
            "user_id": data["user_id"],
            "gift": data["gift"],
            "amount": data["count"],
            "avatar": data["avatar"],
            "diamonds": data.get("diamonds", 0)
        })
        del gift_buffer[key]

async def process_likes(http, to_send):
    for key, data in to_send:
        await http.post(MAIN_API + "like", json={
            "user": data["user"],
            "user_id": key,
            "likes": data["count"],
            "avatar": data["avatar"],
            "diamonds": 1
        })
        del like_buffer[key]

if __name__ == "__main__":
    print("🎥 TikTok listener iniciado")
    client.run()

