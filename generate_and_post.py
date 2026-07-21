"""
Günlük blog yazısı üretip WordPress'e otomatik yayınlayan script.

Akış:
1) topics.txt içinden sırayla bir konu seçilir (state.json ile takip edilir)
2) Google Gemini API (ücretsiz katman) ile o konuda bir yazı ürettirilir
3) (Opsiyonel) Pexels API'den konuya uygun ücretsiz bir görsel indirilir
4) Yazı, WordPress REST API üzerinden "Uygulama Parolası" ile yayınlanır
"""

import os
import json
import requests
from datetime import date

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
WP_URL = os.environ["WP_URL"].rstrip("/")
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")  # yoksa görsel adımı atlanır

# Ücretsiz katmanda en yüksek günlük kotaya sahip model
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

TOPICS_FILE = "topics.txt"
STATE_FILE = "state.json"


def get_next_topic() -> str:
    """topics.txt dosyasından sırayla bir sonraki konuyu döndürür, ilerlemeyi state.json'a kaydeder."""
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]

    if not topics:
        raise ValueError("topics.txt boş görünüyor, en az bir konu ekleyin.")

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {"last_index": -1}

    next_index = (state.get("last_index", -1) + 1) % len(topics)
    state["last_index"] = next_index
    state["last_run"] = str(date.today())

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return topics[next_index]


def generate_post(topic: str) -> dict:
    """Gemini API'yi çağırıp JSON formatında bir blog yazısı üretir."""
    prompt = f"""Sen deneyimli bir Türkçe blog yazarısın. Aşağıdaki konu hakkında SEO uyumlu,
akıcı ve özgün bir blog yazısı hazırla.

Konu: {topic}

Kurallar:
- SADECE geçerli JSON döndür, öncesinde/sonrasında hiçbir açıklama veya kod bloğu işareti ekleme.
- JSON alanları tam olarak şunlar olsun: title, excerpt, content, tags
- content alanı HTML olsun (<h2>, <p>, <ul> gibi etiketler kullan), en az 500 kelime, alt başlıklarla bölünmüş olsun.
- excerpt en fazla 2 cümle olsun.
- tags, 3-5 elemanlı bir string dizisi olsun.
"""

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8},
    }

    resp = requests.post(GEMINI_ENDPOINT, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Gemini bazen yanıtı ```json ... ``` bloğuna sarabiliyor, temizleyelim
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()

    return json.loads(text)


def get_or_create_tag_ids(tags):
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    ids = []
    for tag in tags:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags", params={"search": tag}, auth=auth, timeout=30)
        r.raise_for_status()
        results = r.json()
        if results:
            ids.append(results[0]["id"])
        else:
            r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": tag}, auth=auth, timeout=30)
            if r2.status_code == 201:
                ids.append(r2.json()["id"])
    return ids


def upload_featured_image(topic: str):
    """Pexels'ten konuya uygun ücretsiz bir görsel bulup WordPress medya kütüphanesine yükler."""
    if not PEXELS_API_KEY:
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    r = requests.get(
        "https://api.pexels.com/v1/search",
        params={"query": topic, "per_page": 1},
        headers=headers,
        timeout=30,
    )
    if r.status_code != 200 or not r.json().get("photos"):
        return None

    photo_url = r.json()["photos"][0]["src"]["large"]
    img_data = requests.get(photo_url, timeout=30).content

    auth = (WP_USERNAME, WP_APP_PASSWORD)
    media_headers = {
        "Content-Disposition": "attachment; filename=featured.jpg",
        "Content-Type": "image/jpeg",
    }
    r2 = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        headers=media_headers,
        data=img_data,
        auth=auth,
        timeout=60,
    )
    return r2.json()["id"] if r2.status_code == 201 else None


def publish_post(post: dict):
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    payload = {
        "title": post["title"],
        "content": post["content"],
        "excerpt": post.get("excerpt", ""),
        "status": "publish",
    }

    tag_ids = get_or_create_tag_ids(post.get("tags", []))
    if tag_ids:
        payload["tags"] = tag_ids

    media_id = upload_featured_image(post["title"])
    if media_id:
        payload["featured_media"] = media_id

    r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", json=payload, auth=auth, timeout=60)
    r.raise_for_status()
    print("Yayınlandı:", r.json()["link"])


def main():
    topic = get_next_topic()
    print("Bugünkü konu:", topic)
    post = generate_post(topic)
    publish_post(post)


if __name__ == "__main__":
    main()
