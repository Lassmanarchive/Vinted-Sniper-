
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

HEADERS = {
    "User-Agent": "VintedSniper/0.1",
    "Accept": "text/html"
}

MARKETS = [
    {
        "name": "Ralph Lauren Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=150.00&currency=SEK&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 150,
        "currency": "kr",
        "state": Path("seen_ids.txt"),
    },
    {
        "name": "Ralph Lauren Italien",
        "base": "https://www.vinted.it",
        "url": "https://www.vinted.it/catalog?search_text=ralph%20Lauren%20hoodie&price_to=13.00&currency=EUR&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 13,
        "currency": "€",
        "state": Path("seen_ids_it.txt"),
    },
    {
        "name": "Colmar Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Colmar&price_to=250.00&currency=SEK&order=newest_first",
        "brands": ("colmar",),
        "keywords": ("jacka", "jacket", "puffer", "dunjacka", "vinterjacka"),
        "sizes": {"S", "M", "L"},
        "limit": 250,
        "currency": "kr",
        "state": Path("seen_ids_colmar.txt"),
    },
    {
        "name": "Colmar Italien",
        "base": "https://www.vinted.it",
        "url": "https://www.vinted.it/catalog?search_text=Colmar&price_to=25.00&currency=EUR&order=newest_first",
        "brands": ("colmar",),
        "keywords": ("giacca", "giubbotto", "piumino", "cappotto", "jacket", "puffer", "coat"),
        "sizes": {"S", "M", "L"},
        "limit": 25,
        "currency": "€",
        "state": Path("seen_ids_colmar_it.txt"),
    },
    {
        "name": "J.Lindeberg Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=J.Lindeberg&price_to=250.00&currency=SEK&order=newest_first",
        "brands": ("j.lindeberg", "j lindeberg", "jlindeberg"),
        "keywords": ("jacka", "jacket", "puffer", "dunjacka", "vinterjacka", "coat"),
        "sizes": {"S", "M", "L"},
        "limit": 250,
        "currency": "kr",
        "state": Path("seen_ids_jl.txt"),
    },
    {
        "name": "J.Lindeberg Italien",
        "base": "https://www.vinted.it",
        "url": "https://www.vinted.it/catalog?search_text=J.Lindeberg&price_to=25.00&currency=EUR&order=newest_first",
        "brands": ("j.lindeberg", "j lindeberg", "jlindeberg"),
        "keywords": ("giacca", "giubbotto", "piumino", "cappotto", "jacket", "puffer", "coat"),
        "sizes": {"S", "M", "L"},
        "limit": 25,
        "currency": "€",
        "state": Path("seen_ids_jl_it.txt"),
    },
    {
        "name": "Acne Studios Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Acne%20Studios%20hoodie&price_to=250.00&currency=SEK&order=newest_first",
        "brands": ("acne studios", "acne"),
        "keywords": ("hoodie", "hooded sweatshirt", "sweatshirt"),
        "sizes": {"S", "M", "L"},
        "limit": 250,
        "currency": "kr",
        "state": Path("seen_ids_acne.txt"),
    },
    {
        "name": "Acne Studios Italien",
        "base": "https://www.vinted.it",
        "url": "https://www.vinted.it/catalog?search_text=Acne%20Studios%20hoodie&price_to=25.00&currency=EUR&order=newest_first",
        "brands": ("acne studios", "acne"),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L"},
        "limit": 25,
        "currency": "€",
        "state": Path("seen_ids_acne_it.txt"),
    },
]


def parse_price(text):
    match = re.search(
        r'(\d[\d\s.]*,\d{2})\s*(?:kr|€|EUR)',
        text
    )

    if not match:
        return None

    return float(
        match.group(1)
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )


def scan_market(market):
    print("Bevakar:", market["name"])

    response = requests.get(
        market["url"],
        headers=HEADERS,
        timeout=20
    )

    print(market["name"], "HTTP-status:", response.status_code)
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
        price = parse_price(text)

        if price is None or price > market["limit"]:
            continue

        title = re.split(
            r'\d[\d\s.]*,\d{2}\s*(?:kr|€|EUR)',
            text
        )[0]
        title = re.sub(r'^\d+\s*', '', title).strip()

        searchable = (text + " " + href).lower()

        if not any(
            brand in searchable
            for brand in market["brands"]
        ):
            continue

        if not any(
            word in searchable
            for word in market["keywords"]
        ):
            continue

        size_match = re.search(
            r'(?<![A-Z])(XXL|XS|XL|S|M|L)(?![A-Z])',
            text.upper()
        )

        if not size_match:
            continue

        size = size_match.group(1)

        if size not in market["sizes"]:
            continue

        item_id_match = re.search(r'/items/(\d+)', href)

        if not item_id_match:
            continue

        item_id = item_id_match.group(1)

        candidates[item_id] = {
            "title": title,
            "size": size,
            "price": price,
            "url": urljoin(market["base"], href)
        }

    print(
        market["name"],
        "matchande annonser:",
        len(candidates)
    )

    state_file = market["state"]

    if not state_file.exists():
        state_file.write_text(
            "\n".join(candidates.keys()),
            encoding="utf-8"
        )
        print(
            market["name"],
            "första körningen: befintliga annonser sparade."
        )
        return

    known_ids = set(
        state_file.read_text(encoding="utf-8").splitlines()
    )

    new_count = 0

    for item_id, item in candidates.items():
        if item_id in known_ids:
            continue

        message = (
            f"🔥 **NYTT VINTED-FYND – {market['name']}!**\n"
            f"**{item['title']}**\n"
            f"Storlek: {item['size']}\n"
            f"Pris: {item['price']:.2f} {market['currency']}\n"
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
            state_file.write_text(
                "\n".join(sorted(known_ids)),
                encoding="utf-8"
            )
            new_count += 1

    print(market["name"], "nya notiser:", new_count)


if not WEBHOOK:
    raise SystemExit("Discord-webhook saknas.")

for market in MARKETS:
    try:
        scan_market(market)
    except Exception as error:
        print("Fel i", market["name"], ":", error)

print("Bevakningen är klar.")
