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

BAD_CONDITION_TERMS = (
    "defekt", "trasig", "trasigt", "hål", "fläck", "fläckig",
    "missfärgad", "sliten", "nopprig", "reva", "sprucken",
    "skadad", "skadat",
    "damaged", "defective", "broken", "stained", "stain",
    "worn out", "torn", "ripped", "faded", "pilling",
    "hole", "holes",
    "difettoso", "strappato", "macchiato", "rovinato",
    "usurato", "macchia",
    "uszkodzony", "dziura", "plama", "przetarty",
    "zniszczony",
    "hullet", "plet", "plettet", "slidt",
    "ødelagt", "beskadiget",
)

MARKETS = [
    # RALPH LAUREN HOODIES
    {
        "name": "Ralph Lauren Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=199.00&currency=SEK&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids.txt"),
    },
    {
        "name": "Ralph Lauren Polen",
        "base": "https://www.vinted.pl",
        "url": "https://www.vinted.pl/catalog?search_text=ralph%20Lauren%20hoodie&price_to=60.00&currency=PLN&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "bluza", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 60,
        "currency": "zł",
        "state": Path("seen_ids_rl_pl.txt"),
    },
    {
        "name": "Ralph Lauren Danmark",
        "base": "https://www.vinted.dk",
        "url": "https://www.vinted.dk/catalog?search_text=ralph%20Lauren%20hoodie&price_to=100.00&currency=DKK&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "sweatshirt", "hættetrøje"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 100,
        "currency": "kr",
        "state": Path("seen_ids_rl_dk.txt"),
    },

    # HOLLISTER HOODIES
    {
        "name": "Hollister hoodies Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Hollister%20hoodie&price_to=199.00&currency=SEK&order=newest_first",
        "brands": ("hollister",),
        "keywords": ("hoodie", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids_hollister.txt"),
    },

    # RALPH LAUREN SWEATERS
    {
        "name": "Ralph Lauren sweaters Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Ralph%20Lauren%20sweater&price_to=199.00&currency=SEK&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("sweater", "jumper", "knit", "knitwear", "stickad", "tröja", "pullover"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids_rl_sweater.txt"),
    },

    # SUPERDRY HOODIES
    {
        "name": "Superdry hoodies Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Superdry%20hoodie&price_to=199.00&currency=SEK&order=newest_first",
        "brands": ("superdry",),
        "keywords": ("hoodie", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids_superdry.txt"),
    },

    # PATAGONIA VÄSTAR
    {
        "name": "Patagonia västar Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Patagonia&price_to=400.00&currency=SEK&order=newest_first",
        "brands": ("patagonia",),
        "keywords": ("väst", "fleeceväst", "vest", "gilet"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 400,
        "currency": "kr",
        "state": Path("seen_ids_patagonia.txt"),
    },
    {
        "name": "Patagonia västar Polen",
        "base": "https://www.vinted.pl",
        "url": "https://www.vinted.pl/catalog?search_text=Patagonia&price_to=200.00&currency=PLN&order=newest_first",
        "brands": ("patagonia",),
        "keywords": ("kamizelka", "bezrękawnik", "vest"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 200,
        "currency": "zł",
        "state": Path("seen_ids_patagonia_pl.txt"),
    },
    {
        "name": "Patagonia västar Danmark",
        "base": "https://www.vinted.dk",
        "url": "https://www.vinted.dk/catalog?search_text=Patagonia&price_to=335.00&currency=DKK&order=newest_first",
        "brands": ("patagonia",),
        "keywords": ("vest", "fleecevest"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 335,
        "currency": "kr",
        "state": Path("seen_ids_patagonia_dk.txt"),
    },

    # RALPH LAUREN DUNJACKOR
    {
        "name": "Ralph Lauren dunjackor Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Ralph%20Lauren%20down%20jacket&price_to=700.00&currency=SEK&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("dunjacka", "dun", "down jacket", "down coat", "puffer", "puffjacka"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 700,
        "currency": "kr",
        "state": Path("seen_ids_rl_down.txt"),
    },
    {
        "name": "Ralph Lauren dunjackor Polen",
        "base": "https://www.vinted.pl",
        "url": "https://www.vinted.pl/catalog?search_text=Ralph%20Lauren%20kurtka%20puchowa&price_to=320.00&currency=PLN&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("kurtka puchowa", "puchowa", "puch", "down jacket", "puffer"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 320,
        "currency": "zł",
        "state": Path("seen_ids_rl_down_pl.txt"),
    },
    {
        "name": "Ralph Lauren dunjackor Danmark",
        "base": "https://www.vinted.dk",
        "url": "https://www.vinted.dk/catalog?search_text=Ralph%20Lauren%20dunjakke&price_to=535.00&currency=DKK&order=newest_first",
        "brands": ("ralph lauren",),
        "keywords": ("dunjakke", "dun", "down jacket", "puffer"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 535,
        "currency": "kr",
        "state": Path("seen_ids_rl_down_dk.txt"),
    },

    # COLMAR
    {
        "name": "Colmar Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Colmar&price_to=300.00&currency=SEK&order=newest_first",
        "brands": ("colmar",),
        "keywords": ("jacka", "jacket", "puffer", "dunjacka", "vinterjacka"),
        "sizes": {"S", "M", "L"},
        "limit": 300,
        "currency": "kr",
        "state": Path("seen_ids_colmar.txt"),
    },
    {
        "name": "Colmar Polen",
        "base": "https://www.vinted.pl",
        "url": "https://www.vinted.pl/catalog?search_text=Colmar%20jacket&price_to=100.00&currency=PLN&order=newest_first",
        "brands": ("colmar",),
        "keywords": ("kurtka", "puchowa", "zimowa", "jacket", "puffer"),
        "sizes": {"S", "M", "L"},
        "limit": 100,
        "currency": "zł",
        "state": Path("seen_ids_colmar_pl.txt"),
    },
    {
        "name": "Colmar Danmark",
        "base": "https://www.vinted.dk",
        "url": "https://www.vinted.dk/catalog?search_text=Colmar%20jacket&price_to=170.00&currency=DKK&order=newest_first",
        "brands": ("colmar",),
        "keywords": ("jakke", "dunjakke", "vinterjakke", "jacket", "puffer"),
        "sizes": {"S", "M", "L"},
        "limit": 170,
        "currency": "kr",
        "state": Path("seen_ids_colmar_dk.txt"),
    },

    # J.LINDEBERG
    {
        "name": "J.Lindeberg Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=J.Lindeberg&price_to=300.00&currency=SEK&order=newest_first",
        "brands": ("j.lindeberg", "j lindeberg", "jlindeberg"),
        "keywords": ("jacka", "jacket", "puffer", "dunjacka", "vinterjacka", "coat"),
        "sizes": {"S", "M", "L"},
        "limit": 300,
        "currency": "kr",
        "state": Path("seen_ids_jl.txt"),
    },
    {
        "name": "J.Lindeberg Polen",
        "base": "https://www.vinted.pl",
        "url": "https://www.vinted.pl/catalog?search_text=J.Lindeberg%20jacket&price_to=100.00&currency=PLN&order=newest_first",
        "brands": ("j.lindeberg", "j lindeberg", "jlindeberg"),
        "keywords": ("kurtka", "puchowa", "zimowa", "jacket", "puffer", "coat"),
        "sizes": {"S", "M", "L"},
        "limit": 100,
        "currency": "zł",
        "state": Path("seen_ids_jl_pl.txt"),
    },
    {
        "name": "J.Lindeberg Danmark",
        "base": "https://www.vinted.dk",
        "url": "https://www.vinted.dk/catalog?search_text=J.Lindeberg%20jacket&price_to=170.00&currency=DKK&order=newest_first",
        "brands": ("j.lindeberg", "j lindeberg", "jlindeberg"),
        "keywords": ("jakke", "dunjakke", "vinterjakke", "jacket", "puffer", "coat"),
        "sizes": {"S", "M", "L"},
        "limit": 170,
        "currency": "kr",
        "state": Path("seen_ids_jl_dk.txt"),
    },

    # ACNE STUDIOS
    {
        "name": "Acne Studios Sverige",
        "base": "https://www.vinted.se",
        "url": "https://www.vinted.se/catalog?search_text=Acne%20Studios%20hoodie&price_to=599.00&currency=SEK&order=newest_first",
        "brands": ("acne studios", "acne"),
        "keywords": ("hoodie", "hooded sweatshirt", "sweatshirt"),
        "sizes": {"S", "M", "L"},
        "limit": 599,
        "currency": "kr",
        "state": Path("seen_ids_acne.txt"),
    },
    {
        "name": "Acne Studios Polen",
        "base": "https://www.vinted.pl",
        "url": "https://www.vinted.pl/catalog?search_text=Acne%20Studios%20hoodie&price_to=100.00&currency=PLN&order=newest_first",
        "brands": ("acne studios", "acne"),
        "keywords": ("hoodie", "bluza", "sweatshirt"),
        "sizes": {"S", "M", "L"},
        "limit": 100,
        "currency": "zł",
        "state": Path("seen_ids_acne_pl.txt"),
    },
    {
        "name": "Acne Studios Danmark",
        "base": "https://www.vinted.dk",
        "url": "https://www.vinted.dk/catalog?search_text=Acne%20Studios%20hoodie&price_to=170.00&currency=DKK&order=newest_first",
        "brands": ("acne studios", "acne"),
        "keywords": ("hoodie", "sweatshirt", "hættetrøje"),
        "sizes": {"S", "M", "L"},
        "limit": 170,
        "currency": "kr",
        "state": Path("seen_ids_acne_dk.txt"),
    },
]


def parse_price(text):
    match = re.search(
        r'(\d[\d\s.,]*[,.]\d{2})\s*(?:kr\.?|€|EUR|zł)',
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    raw_price = match.group(1).replace(" ", "")

    if "," in raw_price:
        raw_price = raw_price.replace(".", "").replace(",", ".")

    return float(raw_price)


def has_bad_condition(text):
    searchable = text.lower()

    return any(
        re.search(
            rf"(?<!\w){re.escape(term)}(?!\w)",
            searchable
        )
        for term in BAD_CONDITION_TERMS
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
            r'\d[\d\s.,]*[,.]\d{2}\s*(?:kr\.?|€|EUR|zł)',
            text,
            flags=re.IGNORECASE
        )[0]
        title = re.sub(r'^\d+\s*', '', title).strip()

        searchable = (text + " " + href).lower()

        if has_bad_condition(searchable):
            continue

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