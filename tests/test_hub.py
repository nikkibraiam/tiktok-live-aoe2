import pytest

import main


@pytest.fixture
def hub(monkeypatch):
    # Avatar lookup scrapes TikTok; keep tests offline.
    monkeypatch.setattr(main, "avatar_from_profile", lambda username: None)
    for vm in main.VMS.values():
        vm["like_buffer"].clear()
    http = main.app.test_client()
    bots = {}
    for name in ("vm1", "vm2"):
        bots[name] = main.socketio.test_client(main.app)
        bots[name].emit("register", {"bot": name})
    yield http, bots
    for bot in bots.values():
        bot.disconnect()


def commands(bot):
    return [e["args"][0] for e in bot.get_received() if e["name"] == "command"]


def test_loads_both_vm_configs_regardless_of_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    assert set(main.load_VMS()) == {"vm1", "vm2"}


def test_gift_is_routed_only_to_its_side(hub):
    http, bots = hub

    http.post("/gift", json={"user": "ana", "userId": "ana01", "gift": "TikTok", "amount": 3})

    assert commands(bots["vm1"]) == [{"action": "barracks", "unit": "e", "amount": 3}]
    assert commands(bots["vm2"]) == []


def test_gift_for_the_other_side(hub):
    http, bots = hub

    http.post("/gift", json={"user": "bob", "userId": "bob01", "gift": "GG", "amount": 1})

    assert commands(bots["vm1"]) == []
    assert len(commands(bots["vm2"])) == 1


def test_unknown_gift_is_ignored(hub):
    http, bots = hub

    r = http.post("/gift", json={"user": "ana", "userId": "ana01", "gift": "Not a gift"})

    assert r.status_code == 200
    assert commands(bots["vm1"]) == commands(bots["vm2"]) == []


def test_likes_accumulate_per_user_until_threshold(hub):
    http, bots = hub  # vm1 spawns one unit every 20 likes

    http.post("/like", json={"user": "ana", "userId": "ana01", "likes": 15})
    assert commands(bots["vm1"]) == []

    http.post("/like", json={"user": "ana", "userId": "ana01", "likes": 30})
    assert commands(bots["vm1"]) == [{"action": "barracks", "unit": "s", "amount": 2}]
    assert main.VMS["vm1"]["like_buffer"]["ana"] == 5

    http.post("/like", json={"user": "bob", "userId": "bob01", "likes": 5})
    assert commands(bots["vm1"]) == []


def test_comment_keyword_trains_unit_on_matching_side(hub):
    http, bots = hub

    http.post("/comment", json={"user": "ana", "userId": "ana01", "message": "Soldado"})

    assert commands(bots["vm1"]) == []
    assert commands(bots["vm2"]) == [{"action": "barracks", "unit": "s", "amount": 1}]
