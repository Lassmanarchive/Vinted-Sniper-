import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


BAD_CONDITION_TERMS = (
    "trasig",
    "sönder",
    "defekt",
    "fläck",
    "fläckig",
    "missfärg",
    "hål",
    "reva",
    "sliten",
    "slitage",
    "noppig",
    "noppor",
    "skada",
    "skadat",
    "broken",
    "damaged",
    "stain",
    "stained",
    "discolor",
    "hole",
    "tear",
    "worn",
    "damaged",
    "pilling",
    "uszkodz",
    "plama",
    "dziura",
    "rozdar",
    "zuży",
    "plet",
    "hullet",
    "revet",
    "slidt",
    "fläckar",
)


MARKETS = [
    # =========================
    # RALPH LAUREN – SWEDEN
    # =========================
    {
        "name": "Ralph Lauren Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=ralph%20Lauren%20hoodie"
            "&price_to=199.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids.txt"),
    },

    # =========================
    # RALPH LAUREN – SWEATERS
    # =========================
    {
        "name": "Ralph Lauren sweaters Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=Ralph%20Lauren%20sweater"
            "&price_to=199.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": (
            "sweater",
            "jumper",
            "knit",
            "knitwear",
            "stickad",
            "tröja",
            "pullover",
        ),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids_rl_sweater.txt"),
    },

    # =========================
    # HOLLISTER – SWEDEN
    # =========================
    {
        "name": "Hollister hoodies Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=Hollister%20hoodie"
            "&price_to=199.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("hollister",),
        "keywords": ("hoodie", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids_hollister.txt"),
    },

    # =========================
    # SUPERDRY – SWEDEN
    # =========================
    {
        "name": "Superdry hoodies Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=Superdry%20hoodie"
            "&price_to=199.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("superdry",),
        "keywords": ("hoodie", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 199,
        "currency": "kr",
        "state": Path("seen_ids_superdry.txt"),
    },

    # =========================
    # RALPH LAUREN – DUNJACKOR
    # =========================
    {
        "name": "Ralph Lauren dunjackor Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=Ralph%20Lauren%20down%20jacket"
            "&price_to=700.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": (
            "dunjacka",
            "dun",
            "down jacket",
            "down coat",
            "puffer",
            "puffjacka",
        ),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 700,
        "currency": "kr",
        "state": Path("seen_ids_rl_down.txt"),
    },

    # =========================
    # PATAGONIA – VÄSTAR
    # =========================
    {
        "name": "Patagonia västar Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=Patagonia"
            "&price_to=400.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("patagonia",),
        "keywords": (
            "väst",
            "fleeceväst",
            "vest",
            "gilet",
        ),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 400,
        "currency": "kr",
        "state": Path("seen_ids_patagonia.txt"),
    },

    # =========================
    # COLMAR – SWEDEN
    # =========================
    {
        "name": "Colmar Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=Colmar"
            "&price_to=300.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": ("colmar",),
        "keywords": (
            "jacka",
            "jacket",
            "puffer",
            "dunjacka",
            "vinterjacka",
        ),
        "sizes": {"S", "M", "L"},
        "limit": 300,
        "currency": "kr",
        "state": Path("seen_ids_colmar.txt"),
    },

    # =========================
    # J.LINDEBERG – SWEDEN
    # =========================
    {
        "name": "J.Lindeberg Sverige",
        "base": "https://www.vinted.se",
        "url": (
            "https://www.vinted.se/catalog?"
            "search_text=J.Lindeberg"
            "&price_to=300.00"
            "&currency=SEK"
            "&order=newest_first"
        ),
        "brands": (
            "j.lindeberg",
            "j lindeberg",
            "jlindeberg",
        ),
        "keywords": (
            "jacka",
            "jacket",
            "puffer",
            "dunjacka",
            "vinterjacka",
            "coat",
        ),
        "sizes": {"S", "M", "L"},
        "limit": 300,
        "currency": "kr",
        "state": Path("seen_ids_jl.txt"),
    },

    # =========================
    # RALPH LAUREN – POLEN
    # =========================
    {
        "name": "Ralph Lauren Polen",
        "base": "https://www.vinted.pl",
        "url": (
            "https://www.vinted.pl/catalog?"
            "search_text=ralph%20Lauren%20hoodie"
            "&price_to=60.00"
            "&currency=PLN"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 60,
        "currency": "zł",
        "state": Path("seen_ids_rl_pl.txt"),
    },

    # =========================
    # RALPH LAUREN – DANMARK
    # =========================
    {
        "name": "Ralph Lauren Danmark",
        "base": "https://www.vinted.dk",
        "url": (
            "https://www.vinted.dk/catalog?"
            "search_text=ralph%20Lauren%20hoodie"
            "&price_to=100.00"
            "&currency=DKK"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": ("hoodie", "felpa", "sweatshirt"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 100,
        "currency": "kr",
        "state": Path("seen_ids_rl_dk.txt"),
    },

    # =========================
    # PATAGONIA – POLEN
    # =========================
    {
        "name": "Patagonia Polen",
        "base": "https://www.vinted.pl",
        "url": (
            "https://www.vinted.pl/catalog?"
            "search_text=Patagonia"
            "&price_to=200.00"
            "&currency=PLN"
            "&order=newest_first"
        ),
        "brands": ("patagonia",),
        "keywords": ("vest", "gilet", "fleece", "väst"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 200,
        "currency": "zł",
        "state": Path("seen_ids_patagonia_pl.txt"),
    },

    # =========================
    # PATAGONIA – DANMARK
    # =========================
    {
        "name": "Patagonia Danmark",
        "base": "https://www.vinted.dk",
        "url": (
            "https://www.vinted.dk/catalog?"
            "search_text=Patagonia"
            "&price_to=335.00"
            "&currency=DKK"
            "&order=newest_first"
        ),
        "brands": ("patagonia",),
        "keywords": ("vest", "gilet", "fleece", "väst"),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 335,
        "currency": "kr",
        "state": Path("seen_ids_patagonia_dk.txt"),
    },

    # =========================
    # RALPH LAUREN DUN – POLEN
    # =========================
    {
        "name": "Ralph Lauren dunjackor Polen",
        "base": "https://www.vinted.pl",
        "url": (
            "https://www.vinted.pl/catalog?"
            "search_text=Ralph%20Lauren%20down%20jacket"
            "&price_to=320.00"
            "&currency=PLN"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": (
            "dunjacka",
            "dun",
            "down jacket",
            "down coat",
            "puffer",
            "puffjacka",
        ),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 320,
        "currency": "zł",
        "state": Path("seen_ids_rl_down_pl.txt"),
    },

    # =========================
    # RALPH LAUREN DUN – DANMARK
    # =========================
    {
        "name": "Ralph Lauren dunjackor Danmark",
        "base": "https://www.vinted.dk",
        "url": (
            "https://www.vinted.dk/catalog?"
            "search_text=Ralph%20Lauren%20down%20jacket"
            "&price_to=535.00"
            "&currency=DKK"
            "&order=newest_first"
        ),
        "brands": ("ralph lauren",),
        "keywords": (
            "dunjacka",
            "dun",
            "down jacket",
            "down coat",
            "puffer",
            "puffjacka",
        ),
        "sizes": {"S", "M", "L", "XL"},
        "limit": 535,
        "currency": "kr",
        "state": Path("seen_ids_rl_down_dk.txt"),
    },

    # =========================
    # COLMAR – POLEN
    # =========================
    {
        "name": "Colmar Polen",
        "base": "https://www.vinted.pl",
        "url": (
            "https://www.vinted.pl/catalog?"
            "search_text=Colmar"
            "&price_to=100.00"
            "&currency=PLN"
            "&order=newest_first"
        ),
        "brands": ("colmar",),
        "keywords": (
            "jacka",
            "jacket",
            "puffer",
            "dunjacka",
            "vinterjacka",
        ),
        "sizes": {"S", "M", "L"},
        "limit": 100,
        "currency": "zł",
        "state": Path("seen_ids_colmar_pl.txt"),
    },

    # =========================
    # COLMAR – DANMARK
    # =========================
    {
        "name": "Colmar Danmark",
        "base": "https://www.vinted.dk",
        "url": (
            "https://www.vinted.dk/catalog?"
            "search_text=Colmar"
            "&price_to=170.00"
            "&currency=DKK"
            "&order=newest_first"
        ),
        "brands": ("colmar",),
        "keywords": (
            "jacka",
            "jacket",
            "puffer",
            "dunjacka",
            "vinterjacka",
        ),
        "sizes": {"S", "M", "L"},
        "limit": 170,
        "currency": "kr",
        "state": Path("seen_ids_colmar_dk.txt"),
    },

    # =========================
    # J.LINDEBERG – POLEN
    # =========================
    {
        "name": "J.Lindeberg Polen",
        "base": "https://www.vinted.pl",
        "url": (
            "https://www.vinted.pl/catalog?"
            "search_text=J.Lindeberg"
            "&price_to=100.00"
            "&currency=PLN"
            "&order=newest_first"
        ),
        "brands": (
            "j.lindeberg",
            "j lindeberg",
            "jlindeberg",
        ),
        "keywords": (
            "jacka",
            "jacket",
            "puffer",
            "dunjacka",
            "vinterjacka",
            "coat",
        ),
        "sizes": {"S", "M", "L"},
        "limit": 100,
        "currency": "zł",
        "state": Path("seen_ids_jl_pl.txt"),
    },

    # =========================
    # J.LINDEBERG – DANMARK
    # =========================
    {
        "name": "J.Lindeberg Danmark",
        "base": "https://www.vinted.dk",
        "url": (
            "https://www.vinted.dk/catalog?"
            "search_text=J.Lindeberg"
            "&price_to=170.00"
            "&currency=DKK"
            "&order=newest_first"
        ),
        "brands": (
            "j.lindeberg",
            "j lindeberg",
            "jlindeberg",
        ),
        "keywords": (
            "jacka",
            "jacket",
            "puffer",
            "dunjacka",
            "vinterjacka",
            "coat",
        ),
        "sizes": {"S", "M", "L"},
        "limit": 170,
        "currency": "kr",
        "state": Path("seen_ids_jl_dk.txt"),
    },
]


def parse_price(text):
    if not text:
        return None

    text = text.replace("\xa0", " ")
    text = text.replace(",", ".")

    matches = re.findall(r"\d+(?:\.\d+)?", text)

    if not matches:
        return None

    try:
        return float(matches[0])
    except ValueError:
        return None


def has_bad_condition(text):
    text = text.lower()

    return any(term in text for term in BAD_CONDITION_TERMS)


def load_seen(path):
    if not path.exists():
        return set()

    try:
        return set(path.read_text(encoding="utf-8").splitlines())
    except Exception:
        return set()


def save_seen(path, seen):
    path.write_text(
        "\n".join(sorted(seen)),
        encoding="utf-8",
    )


def send_discord(item):
    if not DISCORD_WEBHOOK:
        print("DISCORD_WEBHOOK saknas.")
        return

    payload = {
        "content": (
            f"🔥 **NY VINTED-TRÄFF**\n"
            f"**{item['title']}**\n"
            f"💰 {item['price']}\n"
            f"📏 Storlek: {item['size']}\n"
            f"🌍 {item['market']}\n"
            f"🔗 {item['url']}"
        )
    }

    try:
        response = requests.post(
            DISCORD_WEBHOOK,
            json=payload,
            timeout=20,
        )

        if response.status_code not in (200, 204):
            print(
                "Discord-fel:",
                response.status_code,
                response.text[:300],
            )

    except Exception as exc:
        print("Discord exception:", exc)


def scan_market(market):
    print(f"\n🔎 {market['name']}")

    try:
        response = requests.get(
            market["url"],
            headers=HEADERS,
            timeout=30,
        )

        print(
            f"HTTP {response.status_code} | "
            f"{market['name']}"
        )

        if response.status_code != 200:
            return

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        seen = load_seen(market["state"])

        links = soup.select('a[href*="/items/"]')

        print(
            f"Hittade {len(links)} möjliga annonser "
            f"på {market['name']}"
        )

        new_count = 0

        for link in links:
            href = link.get("href")

            if not href:
                continue

            if href.startswith("/"):
                item_url = market["base"] + href
            else:
                item_url = href

            item_id_match = re.search(
                r"/items/(\d+)",
                item_url,
            )

            if not item_id_match:
                continue

            item_id = item_id_match.group(1)

            if item_id in seen:
                continue

            text = link.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            text_lower = text.lower()

            # Brand
            if not any(
                brand in text_lower
                for brand in market["brands"]
            ):
                continue

            # Keywords
            if not any(
                keyword in text_lower
                for keyword in market["keywords"]
            ):
                continue

            # Bad condition
            if has_bad_condition(text_lower):
                continue

            # Price
            price = parse_price(text)

            if price is None:
                continue

            if price > market["limit"]:
                continue

            # Size
            detected_size = None

            for size in market["sizes"]:
                if re.search(
                    rf"(?<![A-Za-z]){re.escape(size)}(?![A-Za-z])",
                    text,
                    re.IGNORECASE,
                ):
                    detected_size = size
                    break

            if detected_size is None:
                continue

            item = {
                "title": text[:200],
                "price": f"{price:g} {market['currency']}",
                "size": detected_size,
                "market": market["name"],
                "url": item_url,
            }

            print(
                "🔥 MATCH:",
                item["title"],
                "|",
                item["price"],
                "|",
                item["size"],
            )

            send_discord(item)

            seen.add(item_id)
            new_count += 1

        save_seen(market["state"], seen)

        print(
            f"Klart: {market['name']} | "
            f"Nya träffar: {new_count}"
        )

    except Exception as exc:
        print(
            f"❌ Fel i {market['name']}: {exc}"
        )


def main():
    print("🚀 Vinted Sniper startar...")
    print(f"Antal marknader: {len(MARKETS)}")

    for market in MARKETS:
        scan_market(market)

    print("\n✅ Bevakningen är klar.")


if __name__ == "__main__":
    main()