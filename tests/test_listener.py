import asyncio
from types import SimpleNamespace

import tiktok_listener as listener


class FakeHttp:
    def __init__(self):
        self.posts = []

    async def post(self, url, json):
        self.posts.append((url, json))


def gift_event(user_id, gift, repeat=1, streaking=False, streakable=True):
    return SimpleNamespace(
        user=SimpleNamespace(nickname=user_id.title(), unique_id=user_id),
        gift=SimpleNamespace(name=gift, streakable=streakable, diamond_count=1),
        repeat_count=repeat,
        streaking=streaking,
    )


def setup_function():
    listener.gift_buffer.clear()
    listener.like_buffer.clear()


def test_streak_intermediate_events_are_ignored():
    asyncio.run(listener.on_gift(gift_event("ana01", "Rose", repeat=3, streaking=True)))

    assert listener.gift_buffer == {}


def test_gifts_are_merged_per_user_and_gift():
    for repeat in (5, 7):
        asyncio.run(listener.on_gift(gift_event("ana01", "Rose", repeat=repeat)))
    asyncio.run(listener.on_gift(gift_event("bob01", "Rose", repeat=1)))

    assert listener.gift_buffer[("ana01", "Rose")]["count"] == 12
    assert listener.gift_buffer[("bob01", "Rose")]["count"] == 1


def test_flushed_gift_carries_the_user_id_and_leaves_the_buffer():
    asyncio.run(listener.on_gift(gift_event("ana01", "Rose", repeat=4)))
    http = FakeHttp()

    asyncio.run(listener.process_gifts(http, list(listener.gift_buffer.items())))

    url, payload = http.posts[0]
    assert url.endswith("/gift")
    assert payload["userId"] == "ana01"
    assert payload["amount"] == 4
    assert listener.gift_buffer == {}
