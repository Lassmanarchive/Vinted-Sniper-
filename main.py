import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


# =========================================================
# INSTÄLLNINGAR
# =========================================================

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
GLOBAL_SEEN_FILE = Path("seen_global_ids.txt")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

SIZES = {"S", "M", "L", "XL"}

# Titlar som tydligt anger dam- eller barnplagg sorteras bort.
# Vinted anger inte alltid kön, så filtret kan inte garantera 100 % herr.
NON_MENS_TERMS = (
    "women", "woman", "womens", "women's", "ladies",
    "dam", "dammodell", "tjej", "flicka", "girls",
    "girl's", "kids", "kid's", "children", "childrens",
    "barn", "junior", "baby", "newborn", "toddler",
)

BAD_CONDITION_TERMS = (
    "trasig", "sönder", "defekt", "fläck", "fläckig",
    "missfärg", "hål", "reva", "sliten", "slitage",
    "noppig", "noppor", "skada", "skadat",
    "broken", "damaged", "stain", "stained",
    "discolor", "hole", "tear", "worn", "pilling",
    "uszkodz", "plama", "dziura", "rozdar",
    "zuży", "hullet", "revet", "slidt",
)

EXCLUDED_TERMS = (
    "replica", "fake", "kopior", "kostym", "costume",
    "maskerad", "hund", "dog clothes",
)


# =========================================================
# HJÄLPFUNKTIONER FÖR SÖKNINGAR
# =========================================================

def market(
    name,
    brand_header,
    domain,
    search,
    currency_code,
    limit,
    brands,
    required_groups,
    state,
    excluded_terms=None,
):
    return {
        "name": name,
        "brand_header": brand_header,
        "base": f"https://www.{domain}",
        "url": (
            f"https://www.{domain}/catalog?"
            f"search_text={quote(search)}"
            f"&price_to={limit:.2f}"
            f"&currency={currency_code}"
            f"&order=newest_first"
        ),
        "brands": brands,
        "required_groups": required_groups,
        "excluded_terms": excluded_terms or EXCLUDED_TERMS,
        "limit": limit,
        "currency_code": currency_code,
        "currency": "kr" if currency_code in ("SEK", "DKK") else "zł",
        "state": Path(state),
    }


# =========================================================
# SÖKNINGAR
# =========================================================

MARKETS = [

    # RALPH LAUREN USA FLAG-KNIT – separat maxpris 400 kr
    market(
        "Ralph Lauren USA-flag tröjor Sverige",
        "RALPH LAUREN USA FLAG",
        "vinted.se",
        "Polo Ralph Lauren American flag sweater",
        "SEK",
        400,
        ("polo ralph lauren", "ralph lauren"),
        [
            ("sweater", "jumper", "knit", "stickad", "tröja", "pullover"),
            ("american flag", "usa flag", "flag sweater", "flag knit"),
        ],
        "seen_rl_usa_flag_se.txt",
    ),

    # RALPH LAUREN HOODIES
    market(
        "Ralph Lauren hoodies Sverige",
        "RALPH LAUREN",
        "vinted.se",
        "Polo Ralph Lauren hoodie",
        "SEK",
        249,
        ("polo ralph lauren", "ralph lauren"),
        [
            ("hoodie", "sweatshirt", "hooded sweatshirt"),
        ],
        "seen_rl_hoodie_se.txt",
    ),
    market(
        "Ralph Lauren hoodies Polen",
        "RALPH LAUREN",
        "vinted.pl",
        "Polo Ralph Lauren hoodie",
        "PLN",
        60,
        ("polo ralph lauren", "ralph lauren"),
        [("hoodie", "bluza")],
        "seen_rl_hoodie_pl.txt",
    ),
    market(
        "Ralph Lauren hoodies Danmark",
        "RALPH LAUREN",
        "vinted.dk",
        "Polo Ralph Lauren hoodie",
        "DKK",
        100,
        ("polo ralph lauren", "ralph lauren"),
        [("hoodie", "hættetrøje", "sweatshirt")],
        "seen_rl_hoodie_dk.txt",
    ),

    # VANLIGA RALPH LAUREN-STICKADE TRÖJOR
    market(
        "Ralph Lauren klassiska stickade tröjor Sverige",
        "RALPH LAUREN",
        "vinted.se",
        "Polo Ralph Lauren sweater",
        "SEK",
        199,
        ("polo ralph lauren", "ralph lauren"),
        [
            ("sweater", "jumper", "knit", "stickad", "tröja", "pullover"),
            (
                "cable", "flätstickad", "quarter zip", "half zip",
                "polo bear", "vintage", "pony", "knitted",
            ),
        ],
        "seen_rl_sweater_se.txt",
    ),

    # RALPH LAUREN DUNJACKOR
    market(
        "Ralph Lauren dunjackor Sverige",
        "RALPH LAUREN",
        "vinted.se",
        "Polo Ralph Lauren down jacket",
        "SEK",
        849,
        ("polo ralph lauren", "ralph lauren"),
        [("puffer", "down jacket", "down coat", "dunjacka", "dun")],
        "seen_rl_down_se.txt",
    ),
    market(
        "Ralph Lauren dunjackor Polen",
        "RALPH LAUREN",
        "vinted.pl",
        "Polo Ralph Lauren puffer",
        "PLN",
        320,
        ("polo ralph lauren", "ralph lauren"),
        [("puffer", "down jacket", "down coat", "dunjacka", "kurtka puchowa")],
        "seen_rl_down_pl.txt",
    ),
    market(
        "Ralph Lauren dunjackor Danmark",
        "RALPH LAUREN",
        "vinted.dk",
        "Polo Ralph Lauren puffer",
        "DKK",
        535,
        ("polo ralph lauren", "ralph lauren"),
        [("puffer", "down jacket", "down coat", "dunjacka", "dunjakke")],
        "seen_rl_down_dk.txt",
    ),

    # ABERCROMBIE & FITCH PÄLSHOODIES
    market(
        "Abercrombie pälshoodies Sverige",
        "ABERCROMBIE & FITCH",
        "vinted.se",
        "Abercrombie faux fur hoodie",
        "SEK",
        400,
        ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"),
        [
            ("hoodie", "hooded sweatshirt", "sweatshirt"),
            (
                "fur", "faux fur", "fur lined", "fur-lined",
                "sherpa", "päls", "pälsfodrad", "fuskpäls",
            ),
        ],
        "seen_abercrombie_fur.txt",
    ),

    # ABERCROMBIE & FITCH JACKOR – NYTT, MAX 450 KR
    market(
        "Abercrombie & Fitch jackor Sverige",
        "ABERCROMBIE & FITCH JACKA",
        "vinted.se",
        "Abercrombie jacket",
        "SEK",
        450,
        ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"),
        [
            ("jacket", "jacka", "coat", "parka", "vinterjacka", "puffer"),
        ],
        "seen_abercrombie_jackets_se.txt",
        excluded_terms=EXCLUDED_TERMS + (
            "vest", "väst", "gilet", "hoodie",
        ),
    ),

    # PATAGONIA – ENDAST FLEECEVÄSTAR
    market(
        "Patagonia fleecevästar Sverige",
        "PATAGONIA FLEECEVÄST",
        "vinted.se",
        "Patagonia fleece vest",
        "SEK",
        400,
        ("patagonia",),
        [
            ("vest", "väst", "fleecevest", "gilet"),
            ("fleece", "synchilla", "retro-x", "retro x", "pile"),
        ],
        "seen_patagonia_se.txt",
    ),
    market(
        "Patagonia fleecevästar Polen",
        "PATAGONIA FLEECEVÄST",
        "vinted.pl",
        "Patagonia fleece vest",
        "PLN",
        200,
        ("patagonia",),
        [
            ("vest", "gilet", "kamizelka"),
            ("fleece", "synchilla", "retro-x", "polar"),
        ],
        "seen_patagonia_pl.txt",
    ),
    market(
        "Patagonia fleecevästar Danmark",
        "PATAGONIA FLEECEVÄST",
        "vinted.dk",
        "Patagonia fleece vest",
        "DKK",
        335,
        ("patagonia",),
        [
            ("vest", "gilet"),
            ("fleece", "synchilla", "retro-x", "pile"),
        ],
        "seen_patagonia_dk.txt",
    ),

    # COLMAR JACKOR
    market(
        "Colmar jackor Sverige",
        "COLMAR",
        "vinted.se",
        "Colmar jacket",
        "SEK",
        300,
        ("colmar",),
        [("jacka", "jacket", "puffer", "dunjacka", "vinterjacka")],
        "seen_colmar_se.txt",
    ),
    market(
        "Colmar jackor Polen",
        "COLMAR",
        "vinted.pl",
        "Colmar jacket",
        "PLN",
        100,
        ("colmar",),
        [("jacka", "jacket", "puffer", "kurtka", "kurtka puchowa")],
        "seen_colmar_pl.txt",
    ),
    market(
        "Colmar jackor Danmark",
        "COLMAR",
        "vinted.dk",
        "Colmar jacket",
        "DKK",
        170,
        ("colmar",),
        [("jacka", "jacket", "puffer", "vinterjakke")],
        "seen_colmar_dk.txt",
    ),

    # J.LINDEBERG JACKOR – INGA PUFFERS/DUNJACKOR
    market(
        "J.Lindeberg jackor Sverige",
        "J.LINDEBERG",
        "vinted.se",
        "J.Lindeberg jacket",
        "SEK",
        300,
        ("j.lindeberg", "j lindeberg", "jlindeberg"),
        [("jacka", "jacket", "coat", "vinterjacka")],
        "seen_jl_se.txt",
        excluded_terms=EXCLUDED_TERMS + (
            "puffer", "down jacket", "down coat", "dunjacka",
            "dun", "pufferjacka",
        ),
    ),
    market(
        "J.Lindeberg jackor Polen",
        "J.LINDEBERG",
        "vinted.pl",
        "J.Lindeberg jacket",
        "PLN",
        100,
        ("j.lindeberg", "j lindeberg", "jlindeberg"),
        [("jacka", "jacket", "coat", "kurtka")],
        "seen_jl_pl.txt",
        excluded_terms=EXCLUDED_TERMS + (
            "puffer", "down jacket", "down coat", "dunjacka",
            "dun", "pufferjacka",
        ),
    ),
    market(
        "J.Lindeberg jackor Danmark",
        "J.LINDEBERG",
        "vinted.dk",
        "J.Lindeberg jacket",
        "DKK",
        170,
        ("j.lindeberg", "j lindeberg", "jlindeberg"),
        [("jacka", "jacket", "coat", "vinterjakke")],
        "seen_jl_dk.txt",
        excluded_terms=EXCLUDED_TERMS + (
            "puffer", "down jacket", "down coat", "dunjacka",
            "dun", "pufferjacka",
        ),
    ),

    # BARBOUR KLASSISKA JACKOR
    market(
        "Barbour klassiska jackor Sverige",
        "BARBOUR",
        "vinted.se",
        "Barbour jacket",
        "SEK",
        400,
        ("barbour",),
        [
            ("jacka", "jacket", "coat"),
            (
                "wax", "quilted", "bedale", "beaufort", "ashby",
                "liddesdale", "beadnell", "international", "classic",
            ),
        ],
        "seen_barbour_se.txt",
    ),
]


# =========================================================
# TEXT OCH ANNONSER
# =========================================================

def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", text).strip()


def listing_card_text(link):
    pieces = []
    nodes = [link, *link.select("img, [aria-label], [title]")]

    for node in nodes:
        for attr in ("aria-label", "title", "alt"):
            value = node.get(attr)
            if value:
                pieces.append(value)

        visible = node.get_text(" ", strip=True)
        if visible:
            pieces.append(visible)

    current = link

    for _ in range(6):
        current = current.parent
        if current is None:
            break

        item_ids = set()
        for anchor in current.select('a[href*="/items/"]'):
            match = re.search(r"/items/(\d+)", anchor.get("href", ""))
            if match:
                item_ids.add(match.group(1))

        if len(item_ids) > 1:
            continue

        card_parts = [current.get_text(" ", strip=True)]

        for node in current.select("img, [aria-label], [title]"):
            for attr in ("aria-label", "title", "alt"):
                value = node.get(attr)
                if value:
                    card_parts.append(value)

        candidate = " ".join(part for part in card_parts if part)
        if len(candidate) >= 8:
            pieces.append(candidate)
            break

    result = " ".join(dict.fromkeys(pieces))
    return re.sub(r"\s+", " ", result).strip()


def matches_brand(text, brands):
    normalized = normalize_text(text)
    return any(normalize_text(brand) in normalized for brand in brands)


def matches_groups(text, groups):
    normalized = normalize_text(text)

    for group in groups:
        if not any(normalize_text(term) in normalized for term in group):
            return False

    return True


def contains_any_term(text, terms):
    normalized = normalize_text(text)
    return any(normalize_text(term) in normalized for term in terms)


# =========================================================
# PRIS OCH STORLEK
# =========================================================

def parse_price(text, currency_code):
    if not text:
        return None

    normalized = (
        text.replace("\xa0", " ")
        .replace("\u202f", " ")
        .replace(",", ".")
    )

    if currency_code in ("SEK", "DKK"):
        suffix = r"(?:kr\.?|SEK)"
    else:
        suffix = r"(?:zł|PLN)"

    matches = re.findall(
        rf"(\d+(?:\.\d{{1,2}})?)\s*{suffix}",
        normalized,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    try:
        return float(matches[0])
    except ValueError:
        return None


def detect_size(text):
    labeled = re.search(
        r"(?:size|storlek|strl|stl|taille|rozmiar)"
        r"\s*[:\-]?\s*(XL|S|M|L)\b",
        text,
        flags=re.IGNORECASE,
    )

    if labeled:
        return labeled.group(1).upper()

    for size in ("XL", "S", "M", "L"):
        if re.search(rf"(?<![A-Za-z]){size}(?![A-Za-z])", text):
            return size

    return None


# =========================================================
# SPARA SEDDA ANNONSER
# =========================================================

def load_seen(path):
    if not path.exists():
        return set()

    try:
        return set(path.read_text(encoding="utf-8").splitlines())
    except Exception as exc:
        print(f"⚠️ Kunde inte läsa {path}: {exc}")
        return set()


def save_seen(path, seen):
    try:
        path.write_text("\n".join(sorted(seen)), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Kunde inte spara {path}: {exc}")


# =========================================================
# DISCORD
# =========================================================

def send_discord(item):
    if not DISCORD_WEBHOOK:
        print("❌ DISCORD_WEBHOOK saknas.")
        return False

    payload = {
        "content": (
            f"🔥 **{item['brand_header']} – NYTT FYND!**\n"
            f"_{item['market']}_\n\n"
            f"**{item['title'][:180]}**\n"
            f"💰 **{item['price']}**\n"
            f"📏 Storlek: **{item['size']}**\n"
            f"🔗 {item['url']}"
        )
    }

    try:
        response = requests.post(
            DISCORD_WEBHOOK,
            json=payload,
            timeout=20,
        )

        if response.status_code in (200, 204):
            print("✅ Discord-notis skickad.")
            return True

        print("❌ Discord-fel:", response.status_code, response.text[:300])
        return False

    except Exception as exc:
        print("❌ Discord exception:", exc)
        return False


# =========================================================
# SKANNA EN MARKNAD
# =========================================================

def scan_market(config, global_seen):
    print(f"\n🔎 {config['name']}")

    try:
        response = requests.get(
            config["url"],
            headers=HEADERS,
            timeout=30,
        )

        print(f"HTTP {response.status_code} | {config['name']}")

        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        local_seen = load_seen(config["state"])
        global_seen.update(local_seen)

        links = soup.select('a[href*="/items/"]')
        processed_ids = set()

        print(f"Hittade {len(links)} möjliga annonslänkar")

        stats = {
            "Redan sedda": 0,
            "Fel varumärke": 0,
            "Fel plaggtyp/modell": 0,
            "Dam/barn eller ej herr": 0,
            "Dåligt skick": 0,
            "Uteslutet sökord": 0,
            "Pris saknas": 0,
            "För dyr": 0,
            "Storlek saknas": 0,
            "Discord misslyckades": 0,
        }

        new_count = 0

        for link in links:
            href = link.get("href")
            if not href:
                continue

            item_url = config["base"] + href if href.startswith("/") else href
            match = re.search(r"/items/(\d+)", item_url)

            if not match:
                continue

            item_id = match.group(1)

            if item_id in global_seen or item_id in processed_ids:
                stats["Redan sedda"] += 1
                continue

            processed_ids.add(item_id)
            text = listing_card_text(link)

            if not text:
                continue

            if not matches_brand(text, config["brands"]):
                stats["Fel varumärke"] += 1
                continue

            if not matches_groups(text, config["required_groups"]):
                stats["Fel plaggtyp/modell"] += 1
                continue

            if contains_any_term(text, NON_MENS_TERMS):
                stats["Dam/barn eller ej herr"] += 1
                continue

            if contains_any_term(text, BAD_CONDITION_TERMS):
                stats["Dåligt skick"] += 1
                continue

            if contains_any_term(text, config["excluded_terms"]):
                stats["Uteslutet sökord"] += 1
                continue

            price = parse_price(text, config["currency_code"])

            if price is None:
                stats["Pris saknas"] += 1
                continue

            if price > config["limit"]:
                stats["För dyr"] += 1
                continue

            detected_size = detect_size(text)

            if detected_size not in SIZES:
                stats["Storlek saknas"] += 1
                continue

            item = {
                "title": text[:200],
                "price": f"{price:g} {config['currency']}",
                "size": detected_size,
                "market": config["name"],
                "brand_header": config["brand_header"],
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

            if send_discord(item):
                global_seen.add(item_id)
                local_seen.add(item_id)
                save_seen(GLOBAL_SEEN_FILE, global_seen)
                save_seen(config["state"], local_seen)
                new_count += 1
            else:
                stats["Discord misslyckades"] += 1

        save_seen(GLOBAL_SEEN_FILE, global_seen)
        save_seen(config["state"], local_seen)

        print("\n📊 STATISTIK")
        for reason, count in stats.items():
            print(f"{reason}: {count}")

        print(f"Klart: {config['name']} | Nya träffar: {new_count}")

    except Exception as exc:
        print(f"❌ Fel i {config['name']}: {exc}")


# =========================================================
# START
# =========================================================

def main():
    print("🚀 Vinted Sniper startar...")
    print(f"Antal sökningar: {len(MARKETS)}")

    global_seen = load_seen(GLOBAL_SEEN_FILE)

    print(f"Gemensamt sparade annonser: {len(global_seen)}")

    for config in MARKETS:
        scan_market(config, global_seen)

    save_seen(GLOBAL_SEEN_FILE, global_seen)
    print("\n✅ Bevakningen är klar.")


if __name__ == "__main__":
    main()
