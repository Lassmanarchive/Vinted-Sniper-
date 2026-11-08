import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


# =========================
# INSTÄLLNINGAR
# =========================

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

SEEN_FILE = Path("seen_global_ids.txt")

REQUEST_TIMEOUT = 20
DELAY_BETWEEN_SEARCHES = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

MARKETS = {
    "SE": {
        "domain": "www.vinted.se",
        "currency": "SEK",
        "symbol": "kr",
    },
    "PL": {
        "domain": "www.vinted.pl",
        "currency": "PLN",
        "symbol": "zł",
    },
    "FI": {
        "domain": "www.vinted.fi",
        "currency": "EUR",
        "symbol": "€",
    },
    "DK": {
        "domain": "www.vinted.dk",
        "currency": "DKK",
        "symbol": "kr",
    },
}


# =========================
# SÖKNINGAR
# =========================

SEARCHES = []


def add_search(name, query, prices, exclude=None):
    """Lägger till en sökning för de marknader som har ett maxpris."""
    for country, max_price in prices.items():
        SEARCHES.append({
            "name": name,
            "query": query,
            "country": country,
            "max_price": max_price,
            "exclude": exclude or [],
        })


# Ralph Lauren
add_search(
    "Ralph Lauren USA flag sweaters",
    "ralph lauren usa flag sweater",
    {"SE": 400},
)

add_search(
    "Ralph Lauren hoodies",
    "ralph lauren hoodie",
    {"SE": 249, "PL": 60, "DK": 100},
)

add_search(
    "Ralph Lauren classic sweaters",
    "ralph lauren sweater",
    {"SE": 199},
)

add_search(
    "Ralph Lauren down jackets",
    "ralph lauren down jacket",
    {"SE": 849, "PL": 320, "DK": 535},
)

add_search(
    "Ralph Lauren shirts",
    "ralph lauren shirt",
    {"SE": 149, "PL": 58, "FI": 13, "DK": 97},
)


# Abercrombie & Fitch
add_search(
    "Abercrombie faux fur hoodies",
    "abercrombie faux fur hoodie",
    {"SE": 400},
)

add_search(
    "Abercrombie jackets",
    "abercrombie jacket",
    {"SE": 450},
)

add_search(
    "Abercrombie cardigans",
    "abercrombie cardigan",
    {"SE": 400, "PL": 155, "FI": 35, "DK": 260},
)


# Hollister
add_search(
    "Hollister cardigans",
    "hollister cardigan",
    {"SE": 400, "PL": 155, "FI": 35, "DK": 260},
)


# Patagonia
add_search(
    "Patagonia fleece vests",
    "patagonia fleece vest",
    {"SE": 400, "PL": 200, "DK": 335},
)


# Colmar
add_search(
    "Colmar jackets",
    "colmar jacket",
    {"SE": 300, "PL": 100, "DK": 170},
)


# J.Lindeberg
add_search(
    "J.Lindeberg jackets",
    "j lindeberg jacket",
    {"SE": 300, "PL": 100, "DK": 170},
    exclude=["puffer", "down jacket", "down coat"],
)


# Skjortor
add_search(
    "Burberry shirts",
    "burberry shirt",
    {"SE": 200, "PL": 78, "FI": 18, "DK": 130},
)


# Skor
add_search(
    "Lanvin shoes",
    "lanvin shoes",
    {"SE": 700},
)

add_search(
    "Valentino shoes",
    "valentino shoes",
    {"SE": 600},
)

add_search(
    "Maison Margiela GAT",
    "maison margiela gat",
    {"SE": 800},
)

add_search(
    "Adidas Wales Bonner",
    "adidas wales bonner",
    {"SE": 700},
)


# Övrigt
add_search(
    "Barbour classic jackets",
    "barbour jacket",
    {"SE": 400},
)


# =========================
# DISCORD
# =========================

def send_discord(message):
    if not DISCORD_WEBHOOK:
        print("DISCORD_WEBHOOK saknas.")
        return

    try:
        response = requests.post(
            DISCORD_WEBHOOK,
            json={"content": message},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Discord-fel: {error}")


# =========================
# DUBBLETTKONTROLL
# =========================

def load_seen_ids():
    if not SEEN_FILE.exists():
        return set()

    try:
        return set(SEEN_FILE.read_text(encoding="utf-8").splitlines())
    except OSError as error:
        print(f"Kunde inte läsa seen-filen: {error}")
        return set()


def save_seen_ids(seen_ids):
    try:
        SEEN_FILE.write_text(
            "\n".join(sorted(seen_ids)),
            encoding="utf-8",
        )
    except OSError as error:
        print(f"Kunde inte spara seen-filen: {error}")


# =========================
# PRISER
# =========================

def parse_price(text, currency):
    """Försöker hitta priset i en produktannons."""
    if not text:
        return None

    cleaned = text.replace("\xa0", " ").replace(",", ".")

    patterns = [
        r"€\s*(\d+(?:\.\d{1,2})?)",
        r"(\d+(?:\.\d{1,2})?)\s*€",
        r"(\d+(?:\.\d{1,2})?)\s*zł",
        r"zł\s*(\d+(?:\.\d{1,2})?)",
        r"(\d+(?:\.\d{1,2})?)\s*kr",
        r"kr\s*(\d+(?:\.\d{1,2})?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

    return None


# =========================
# VINTED-SÖKNING
# =========================

def build_url(search):
    market = MARKETS[search["country"]]

    params = {
        "search_text": search["query"],
        "price_to": str(search["max_price"]),
        "currency": market["currency"],
        "order": "newest_first",
    }

    return (
        f"https://{market['domain']}/catalog?"
        f"{urlencode(params)}"
    )


def get_item_id(url):
    match = re.search(r"/items/(\d+)", url)
    return match.group(1) if match else None


def get_product_card(link):
    """Hämtar en möjlig annonsruta runt produktlänken."""
    current = link

    for _ in range(5):
        if current.parent:
            current = current.parent

        text = current.get_text(" ", strip=True)

        if text and len(text) > 15:
            return current

    return link


def scan_search(search, seen_ids):
    url = build_url(search)

    print(
        f"Söker: {search['name']} | "
        f"{search['country']} | max {search['max_price']}"
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Kunde inte hämta sidan: {error}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.select('a[href*="/items/"]')

    found_ids = set()

    for link in links:
        href = link.get("href", "")
        item_id = get_item_id(href)

        if not item_id or item_id in found_ids:
            continue

        found_ids.add(item_id)

        if item_id in seen_ids:
            continue

        card = get_product_card(link)
        card_text = card.get_text(" ", strip=True)

        title = link.get_text(" ", strip=True)

        if not title:
            title = card_text[:120]

        # Kontrollera ord som ska uteslutas.
        lower_text = (title + " " + card_text).lower()

        if any(
            word.lower() in lower_text
            for word in search["exclude"]
        ):
            continue

        market = MARKETS[search["country"]]
        price = parse_price(card_text, market["currency"])

        if price is None:
            continue

        if price > search["max_price"]:
            continue

        if href.startswith("/"):
            item_url = f"https://{market['domain']}{href}"
        else:
            item_url = href

        message = (
            f"**NY VINTED-TRÄFF!**\n"
            f"**Sökning:** {search['name']}\n"
            f"**Land:** {search['country']}\n"
            f"**Pris:** {price:g} {market['symbol']}\n"
            f"**Annons:** {title[:150]}\n"
            f"{item_url}"
        )

        send_discord(message)
        seen_ids.add(item_id)

        print(f"Träff: {title} – {price} {market['symbol']}")


# =========================
# START
# =========================

def main():
    print("VINTED SNIPER STARTAR")

    if not DISCORD_WEBHOOK:
        print("VARNING: DISCORD_WEBHOOK saknas.")

    seen_ids = load_seen_ids()

    print(f"Antal sökningar: {len(SEARCHES)}")
    print(f"Redan sparade annonser: {len(seen_ids)}")

    for search in SEARCHES:
        scan_search(search, seen_ids)
        save_seen_ids(seen_ids)
        time.sleep(DELAY_BETWEEN_SEARCHES)

    print("VINTED SNIPER KLAR")


if __name__ == "__main__":
    main()