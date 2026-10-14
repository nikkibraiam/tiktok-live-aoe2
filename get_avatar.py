import json
import os
import re

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_AVATAR_DIR = "overlay/avatars"
os.makedirs(BASE_AVATAR_DIR, exist_ok=True)


def fetch_profile_html(username: str) -> str:
    url = f"https://www.tiktok.com/@{username}"
    r = httpx.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.text


def extract_avatar_thumb(html: str) -> str:
    match = re.search(r'"avatarThumb"\s*:\s*"([^"]+)"', html)
    if not match:
        return ""

    # TikTok escapa la URL como JSON
    raw_url = match.group(1)
    return json.loads(f'"{raw_url}"')


def download_avatar(url: str, save_path: str):
    with httpx.stream("GET", url, headers=HEADERS, timeout=10) as r:
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


def avatar_from_profile(username: str) -> str:

    user_dir = os.path.join(BASE_AVATAR_DIR, username)
    avatar_path = user_dir + ".jpeg"

    # Evita descargar si ya existe
    if os.path.exists(avatar_path):
        print(f"[OK] Avatar ya existe: {avatar_path}")
        return avatar_path

    html = fetch_profile_html(username)
    avatar_url = extract_avatar_thumb(html)

    if not avatar_url:
        print(f"[WARN] No se encontró avatar para {username}")
        return ""
    
    download_avatar(avatar_url, avatar_path)
    print(f"[OK] Avatar guardado en: {avatar_path}")

    return avatar_path


# ===== EJEMPLO =====
if __name__ == "__main__":
    avatar_from_profile("nikkibraiam7")
