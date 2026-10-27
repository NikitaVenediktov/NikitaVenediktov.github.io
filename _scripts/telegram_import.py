"""Импорт постов публичного Telegram-канала в блог.

Читает веб-версию канала (https://t.me/s/<канал>) и складывает каждый пост
в `_posts/telegram/` как запись Jekyll, а картинки — в `assets/telegram/`.
Запускается в GitHub Actions перед сборкой сайта; результат в git не коммитится.

    python _scripts/telegram_import.py underside_ai
"""

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts" / "telegram"
ASSETS_DIR = ROOT / "assets" / "telegram"
USER_AGENT = "Mozilla/5.0 (compatible; site-telegram-import)"
TITLE_MAX = 90
DESCRIPTION_MAX = 200
MAX_PAGES = 200
ALLOWED_TAGS = {"a", "b", "strong", "i", "em", "u", "s", "del", "code", "pre", "br", "blockquote"}
BG_URL = re.compile(r"background-image:url\('([^']+)'\)")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.geturl(), response.read()


def fetch_messages(channel):
    """Все посты канала, от новых к старым, с учётом пагинации ?before=."""
    messages, before = [], None
    for _ in range(MAX_PAGES):
        url = f"https://t.me/s/{channel}" + (f"?before={before}" if before else "")
        final_url, body = fetch(url)
        if "/s/" not in final_url:
            # У канала без постов Telegram не отдаёт веб-версию и редиректит на t.me/<канал>.
            print(f"У канала {channel} нет веб-версии с постами ({final_url})", file=sys.stderr)
            break
        page = BeautifulSoup(body, "html.parser")
        found = page.select(".tgme_widget_message[data-post]")
        if not found:
            break
        messages.extend(reversed(found))
        more = page.select_one(".tme_messages_more[data-before]")
        if not more:
            break
        before = more["data-before"]
    return messages


def clean_text(node):
    """Оставляет в тексте поста только безопасную разметку."""
    for emoji in node.select("tg-emoji, i.emoji"):
        emoji.replace_with(emoji.get_text())
    for tag in node.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue
        href = tag.get("href") if tag.name == "a" else None
        tag.attrs = {"href": href} if href else {}
    return node


def plain_lines(node):
    copy = BeautifulSoup(str(node), "html.parser")
    for br in copy.find_all("br"):
        br.replace_with("\n")
    return [line.strip() for line in copy.get_text().split("\n") if line.strip()]


def shorten(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.:;—- ") + "…"


def drop_first_line(html):
    """Убирает из HTML первую строку текста — она становится заголовком записи."""
    seen_text = False
    for match in re.finditer(r"<br/>|<[^>]+>|[^<]+", html):
        token = match.group()
        if token == "<br/>" and seen_text:
            rest = html[match.end():]
            rest = BeautifulSoup(rest, "html.parser").decode()
            return re.sub(r"^(\s|<br/>)+", "", rest)
        if not token.startswith("<") and token.strip():
            seen_text = True
    return ""


def download(url, name):
    """Скачивает картинку; при ошибке возвращает None, и пост выходит без неё."""
    if url.startswith("//"):
        url = "https:" + url
    try:
        _, data = fetch(url)
    except OSError as error:
        print(f"Не удалось скачать {name}: {error}", file=sys.stderr)
        return None
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / name).write_bytes(data)
    return f"/assets/telegram/{name}"


def convert(message, channel):
    post_id = message["data-post"].split("/")[-1]
    link = f"https://t.me/{channel}/{post_id}"
    time = message.select_one(".tgme_widget_message_date time[datetime]")
    if not time:
        return None
    date = datetime.fromisoformat(time["datetime"])

    text_node = message.select_one(".tgme_widget_message_text")
    lines, body = [], ""
    if text_node:
        clean_text(text_node)
        lines = plain_lines(text_node)
        body = text_node.decode_contents().strip()

    if lines and len(lines[0]) <= TITLE_MAX:
        title, rest = lines[0], lines[1:]
        body = drop_first_line(body)
    elif lines:
        title, rest = shorten(lines[0], TITLE_MAX), lines
    else:
        title, rest = f"Пост в Telegram от {date:%d.%m.%Y}", []
    description = shorten(" ".join(rest), DESCRIPTION_MAX)

    media = []
    for n, photo in enumerate(message.select(".tgme_widget_message_photo_wrap"), 1):
        found = BG_URL.search(photo.get("style", ""))
        if found:
            src = download(found.group(1), f"{post_id}-{n}.jpg")
            if src:
                media.append(f'<p><img src="{{{{ \'{src}\' | relative_url }}}}" alt="" loading="lazy"></p>')
    for n, video in enumerate(message.select(".tgme_widget_message_video_thumb"), 1):
        found = BG_URL.search(video.get("style", ""))
        if found:
            src = download(found.group(1), f"{post_id}-video-{n}.jpg")
            preview = f'<a href="{link}"><img src="{{{{ \'{src}\' | relative_url }}}}" alt="Видео" loading="lazy"></a><br>' if src else ""
            media.append(f'<p>{preview}<a href="{link}">Смотреть видео в Telegram</a></p>')

    # Фигурные скобки из текста поста не должны выполняться как Liquid.
    body = body.replace("{", "&#123;").replace("}", "&#125;")
    front = {
        "layout": "post",
        "title": title,
        "date": date.strftime("%Y-%m-%d %H:%M:%S %z"),
        "source": "Telegram",
        "source_url": link,
    }
    if description:
        front["description"] = description
    header = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in front.items())
    content = "\n".join(media + ([f'<div class="tg-post">{body}</div>'] if body else []))
    return f"{date:%Y-%m-%d}-tg-{post_id}.html", f"---\n{header}\n---\n{content}\n"


def main(channel):
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    imported = 0
    for message in fetch_messages(channel):
        if message.select_one(".tgme_widget_message_forwarded_from"):
            continue  # пересланные посты — не авторские
        converted = convert(message, channel)
        if converted:
            name, text = converted
            (POSTS_DIR / name).write_text(text, encoding="utf-8")
            imported += 1
    print(f"Импортировано постов из @{channel}: {imported}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "underside_ai")
