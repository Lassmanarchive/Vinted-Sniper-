
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
    "trasig", "sönder", "defekt", "fläck", "fläckig",
    "missfärg", "hål", "reva", "sliten", "slitage",
    "noppig", "noppor", "skada", "skadat", "broken",
    "damaged", "stain", "stained", "discolor", "hole",
    "tear", "worn", "pilling", "uszkodz", "plama",
    "dziura", "rozdar", "zuży", "plet", "hullet",
    "revet", "slidt",
)


def market(name, domain, search, currency, limit, brands,
           keywords, sizes, state):
    return {
        "name": name,
        "base": f"https://www.{domain}",
        "url": (
            f"https://www.{domain}/catalog?"
            f"search_text={requests.utils.quote(search)}"
            f"&price_to={limit:.2f}"
            f"&currency={currency}"
            f"&order=newest_first"
        ),
        "brands": brands,
        "keywords": keywords,
        "sizes": sizes,
        "limit": limit,
        "currency": "kr" if currency in ("SEK", "DKK") else "zł",
        "state": Path(state),
    }


SIZES = {"S", "M", "L", "XL"}
JACKET_SIZES = {"S", "M", "L", "XL"}


MARKETS = [
    market(
        "Ralph Lauren Sverige", "vinted.se",
        "ralph Lauren hoodie", "SEK", 199,
        ("ralph lauren",),
        ("hoodie", "felpa", "sweatshirt", "bluza", "hættetrøje"),
        SIZES, "seen_ids.txt"
    ),

    market(
        "Ralph Lauren sweaters Sverige", "vinted.se",
        "Ralph Lauren sweater", "SEK", 199,
        ("ralph lauren",),
        ("sweater", "jumper", "knit", "knitwear",
         "stickad", "tröja", "pullover", "sweter",
         "dzianinowy", "trøje"),
        SIZES, "seen_ids_rl_sweater.txt"
    ),

    market(
        "Hollister hoodies Sverige", "vinted.se",
        "Hollister hoodie", "SEK", 199,
        ("hollister",),
        ("hoodie", "sweatshirt", "bluza", "hættetrøje"),
        SIZES, "seen_ids_hollister.txt"
    ),

    market(
        "Superdry hoodies Sverige", "vinted.se",
        "Superdry hoodie", "SEK", 199,
        ("superdry",),
        ("hoodie", "sweatshirt", "bluza", "hættetrøje"),
        SIZES, "seen_ids_superdry.txt"
    ),

    market(
        "Ralph Lauren dunjackor Sverige", "vinted.se",
        "Ralph Lauren down jacket", "SEK", 700,
        ("ralph lauren",),
        ("dunjacka", "dun", "down jacket", "down coat",
         "puffer", "puffjacka", "kurtka puchowa", "dunjakke"),
        SIZES, "seen_ids_rl_down.txt"
    ),

    market(
        "Patagonia västar Sverige", "vinted.se",
        "Patagonia", "SEK", 400,
        ("patagonia",),
        ("väst", "fleeceväst", "vest", "gilet", "kamizelka"),
        SIZES, "seen_ids_patagonia.txt"
    ),

    market(
        "Colmar Sverige", "vinted.se",
        "Colmar", "SEK", 300,
        ("colmar",),
        ("jacka", "jacket", "puffer", "dunjacka",
         "vinterjacka", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_colmar.txt"
    ),

    market(
        "J.Lindeberg Sverige", "vinted.se",
        "J.Lindeberg", "SEK", 300,
        ("j.lindeberg", "j lindeberg", "jlindeberg"),
        ("jacka", "jacket", "puffer", "dunjacka",
         "vinterjacka", "coat", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_jl.txt"
    ),

    market(
        "Barbour jackor Sverige", "vinted.se",
        "Barbour jacket", "SEK", 400,
        ("barbour",),
        ("jacka", "jacket", "quilted", "wax jacket",
         "vinterjacka", "coat", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_barbour.txt"
    ),

    market(
        "Carhartt hoodies Sverige", "vinted.se",
        "Carhartt hoodie", "SEK", 150,
        ("carhartt", "carhartt wip"),
        ("hoodie", "sweatshirt", "bluza", "hættetrøje"),
        SIZES, "seen_ids_carhartt.txt"
    ),

    market(
        "Woolrich jackor Sverige", "vinted.se",
        "Woolrich jacket", "SEK", 400,
        ("woolrich",),
        ("jacka", "jacket", "parka", "puffer",
         "down jacket", "coat", "vinterjacka", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_woolrich.txt"
    ),

    market(
        "Ralph Lauren Polen", "vinted.pl",
        "ralph Lauren hoodie", "PLN", 60,
        ("ralph lauren",),
        ("hoodie", "felpa", "sweatshirt", "bluza"),
        SIZES, "seen_ids_rl_pl.txt"
    ),

    market(
        "Ralph Lauren Danmark", "vinted.dk",
        "ralph Lauren hoodie", "DKK", 100,
        ("ralph lauren",),
        ("hoodie", "felpa", "sweatshirt", "hættetrøje"),
        SIZES, "seen_ids_rl_dk.txt"
    ),

    market(
        "Patagonia Polen", "vinted.pl",
        "Patagonia", "PLN", 200,
        ("patagonia",),
        ("vest", "gilet", "fleece", "väst", "kamizelka"),
        SIZES, "seen_ids_patagonia_pl.txt"
    ),

    market(
        "Patagonia Danmark", "vinted.dk",
        "Patagonia", "DKK", 335,
        ("patagonia",),
        ("vest", "gilet", "fleece", "väst"),
        SIZES, "seen_ids_patagonia_dk.txt"
    ),

    market(
        "Ralph Lauren dunjackor Polen", "vinted.pl",
        "Ralph Lauren down jacket", "PLN", 320,
        ("ralph lauren",),
        ("dunjacka", "dun", "down jacket", "down coat",
         "puffer", "puffjacka", "kurtka puchowa"),
        SIZES, "seen_ids_rl_down_pl.txt"
    ),

    market(
        "Ralph Lauren dunjackor Danmark", "vinted.dk",
        "Ralph Lauren down jacket", "DKK", 535,
        ("ralph lauren",),
        ("dunjacka", "dun", "down jacket", "down coat",
         "puffer", "puffjacka", "dunjakke"),
        SIZES, "seen_ids_rl_down_dk.txt"
    ),

    market(
        "Colmar Polen", "vinted.pl",
        "Colmar", "PLN", 100,
        ("colmar",),
        ("jacka", "jacket", "puffer", "dunjacka",
         "vinterjacka", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_colmar_pl.txt"
    ),

    market(
        "Colmar Danmark", "vinted.dk",
        "Colmar", "DKK", 170,
        ("colmar",),
        ("jacka", "jacket", "puffer", "dunjacka",
         "vinterjacka", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_colmar_dk.txt"
    ),

    market(
        "J.Lindeberg Polen", "vinted.pl",
        "J.Lindeberg", "PLN", 100,
        ("j.lindeberg", "j lindeberg", "jlindeberg"),
        ("jacka", "jacket", "puffer", "dunjacka",
         "vinterjacka", "coat", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_jl_pl.txt"
    ),

    market(
        "J.Lindeberg Danmark", "vinted.dk",
        "J.Lindeberg", "DKK", 170,
        ("j.lindeberg", "j lindeberg", "jlindeberg"),
        ("jacka", "jacket", "puffer", "dunjacka",
         "vinterjacka", "coat", "kurtka", "jakke"),
        JACKET_SIZES, "seen_ids_jl_dk.txt"
    ),
]


def parse_price(text):
    if not text:
        return None

    text = text.replace("\xa0", " ").replace(",", ".")
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
        encoding="utf-8"
    )


def send_discord(item):
    if not DISCORD_WEBHOOK:
        print("DISCORD_WEBHOOK saknas.")
        return False

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
            timeout=20
        )

        if response.status_code in (200, 204):
            print("✅ Discord-notis skickad.")
            return True

        print(
            "❌ Discord-fel:",
            response.status_code,
            response.text[:300]
        )
        return False

    except Exception as exc:
        print("❌ Discord exception:", exc)
        return False


def scan_market(market_config):
    print(f"\n🔎 {market_config['name']}")

    try:
        response = requests.get(
            market_config["url"],
            headers=HEADERS,
            timeout=30
        )

        print(
            f"HTTP {response.status_code} | "
            f"{market_config['name']}"
        )

        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        seen = load_seen(market_config["state"])
        links = soup.select('a[href*="/items/"]')

        print(
            f"Hittade {len(links)} möjliga annonser "
            f"på {market_config['name']}"
        )

        new_count = 0
        stats = {
            "Redan sedda": 0,
            "Saknar annonstext": 0,
            "Fel varumärke": 0,
            "Fel plaggtyp": 0,
            "Dåligt skick": 0,
            "Pris saknas": 0,
            "För dyr": 0,
            "Storlek saknas": 0,
            "Discord misslyckades": 0,
        }

        for link in links:
            href = link.get("href")

            if not href:
                continue

            if href.startswith("/"):
                item_url = market_config["base"] + href
            else:
                item_url = href

            item_id_match = re.search(r"/items/(\d+)", item_url)

            if not item_id_match:
                continue

            item_id = item_id_match.group(1)

            if item_id in seen:
                stats["Redan sedda"] += 1
                continue

            text = link.get_text(" ", strip=True)

            if not text:
                stats["Saknar annonstext"] += 1
                continue

            text_lower = text.lower()

            if not any(
                brand in text_lower
                for brand in market_config["brands"]
            ):
                stats["Fel varumärke"] += 1
                continue

            if not any(
                keyword in text_lower
                for keyword in market_config["keywords"]
            ):
                stats["Fel plaggtyp"] += 1
                continue

            if has_bad_condition(text_lower):
                stats["Dåligt skick"] += 1
                continue

            price = parse_price(text)

            if price is None:
                stats["Pris saknas"] += 1
                continue

            if price > market_config["limit"]:
                stats["För dyr"] += 1
                continue

            detected_size = None

            for size in market_config["sizes"]:
                if re.search(
                    rf"(?<![A-Za-z]){re.escape(size)}(?![A-Za-z])",
                    text,
                    re.IGNORECASE
                ):
                    detected_size = size
                    break

            if detected_size is None:
                stats["Storlek saknas"] += 1
                continue

            item = {
                "title": text[:200],
                "price": f"{price:g} {market_config['currency']}",
                "size": detected_size,
                "market": market_config["name"],
                "url": item_url,
            }

            print(
                "🔥 MATCH:",
                item["title"],
                "|",
                item["price"],
                "|",
                item["size"]
            )

            if send_discord(item):
                seen.add(item_id)
                new_count += 1
            else:
                stats["Discord misslyckades"] += 1
                print(
                    f"⚠️ Annons {item_id} sparas inte som sedd. "
                    "Den försöks igen vid nästa körning."
                )

        save_seen(market_config["state"], seen)

        print("📊 FELSÖKNINGSSTATISTIK:")
        for reason, count in stats.items():
            print(f"   {reason}: {count}")

        print(
            f"Klart: {market_config['name']} | "
            f"Nya träffar: {new_count}"
        )

    except Exception as exc:
        print(
            f"❌ Fel i {market_config['name']}: {exc}"
        )


def main():
    print("🚀 Vinted Sniper startar...")
    print(f"Antal marknader: {len(MARKETS)}")

    for market_config in MARKETS:
        scan_market(market_config)

    print("\n✅ Bevakningen är klar.")


if __name__ == "__main__":
    main()
 