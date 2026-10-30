
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = (
    "https://www.vinted.se/catalog?"
    "search_text=ralph%20Lauren%20hoodie"
    "&price_to=150.00&currency=SEK&order=newest_first"
)

WEBHOOK = os.getenv("DISCORD_WEBHOOK")
STATE_FILE = Path("seen_ids.txt")
ALLOWED_SIZES = {"S", "M", "L", "XL"}

headers = {
    "User-Agent": "VintedSniper/0.1",
    "Accept": "text/html"
}

response = requests.get(URL, headers=headers, timeout=20)
print("HTTP-status:", response.status_code)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
candidates = {}
seen_links = set()

for link in soup.select('a[href*="/items/"]'):
    href = link.get("href", "")

    if href in seen_links:
        continue
    seen_links.add(href)

    card = link.parent.parent
    if not card:
        continue

    text = card.get_text(" ", strip=True)

    title = re.split(r'\d[\d\s]*,\d{2}\s*kr', text)[0]
    title = re.sub(r'^\d+\s*', '', title).strip()

    price_match = re.search(r'(\d[\d\s]*,\d{2})\s*kr', text)
    if not price_match:
        continue

    price = float(
        price_match.group(1).replace(" ", "").replace(",", ".")
    )

    size_match = re.search(
        r'(?<![A-Z])(XXL|XS|XL|S|M|L)(?![A-Z])',
        title.upper()
    )

    if not size_match:
        continue

    size = size_match.group(1)

    if size not in ALLOWED_SIZES:
        continue
    if "ralph lauren" not in title.lower():
        continue
    if "hoodie" not in href.lower():
        continue
    if price > 150:
        continue

    item_id_match = re.search(r'/items/(\d+)', href)
    if not item_id_match:
        continue

    item_id = item_id_match.group(1)

    candidates[item_id] = {
        "title": title,
        "size": size,
        "price": price,
        "url": urljoin("https://www.vinted.se", href)
    }

print("Matchande annonser:", len(candidates))

# Första körningen: spara befintliga annonser utan att skicka notiser.
if not STATE_FILE.exists():
    STATE_FILE.write_text(
        "\n".join(candidates.keys()),
        encoding="utf-8"
    )
    print("Första körningen: annonser sparade. Inga notiser skickas.")
    raise SystemExit

known_ids = set(
    STATE_FILE.read_text(encoding="utf-8").splitlines()
)

if not WEBHOOK:
    raise SystemExit("Discord-webhook saknas.")

new_count = 0

for item_id, item in candidates.items():
    if item_id in known_ids:
        continue

    message = (
        "🔥 **NYTT VINTED-FYND!**\n"
        f"**{item['title']}**\n"
        f"Storlek: {item['size']}\n"
        f"Pris: {item['price']:.2f} kr\n"
        f"{item['url']}"
    )

    discord_response = requests.post(
        WEBHOOK,
        json={"content": message},
        timeout=20
    )

    print("Discord status:", discord_response.status_code)

    if discord_response.status_code in (200, 204):
        known_ids.add(item_id)
        STATE_FILE.write_text(
            "\n".join(sorted(known_ids)),
            encoding="utf-8"
        )
        new_count += 1
    else:
        print("Kunde inte skicka notis för:", item_id)

print("Nya Discord-notiser:", new_count)
