import os
import re
import time
import random
import unicodedata
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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

BLACK_TERMS = (
    "black", "svart", "svarta", "noir", "czarny", "czarna",
    "czarne", "musta", "sort", "nero", "nera", "nere", "neri",
)
BLUE_TERMS = (
    "blue", "blå", "blått", "blåa", "navy", "marine", "dark blue",
    "niebieski", "niebieska", "sininen", "bla", "blu", "azzurro",
    "azzurra", "blu navy",
)
WHITE_TERMS = (
    "white", "vit", "vita", "vitt", "weiss", "weiß", "bialy",
    "biały", "biala", "valkoinen", "hvid", "bianco", "bianca",
    "bianche", "bianchi",
)

# =========================================================
# HJÄLPFUNKTION FÖR MARKNADER
# =========================================================
def market(name, brand_header, domain, search, currency_code, limit,
           brands, required_groups, state, excluded_terms=None,
           size_mode="clothing"):
    return {
        "name": name,
        "brand_header": brand_header,
        "base": f"https://www.{domain}",
        "url": (
            f"https://www.{domain}/catalog?"
            f"search_text={quote(search)}"
            f"&price_to={limit:.2f}"
            f"&currency={currency_code}"
            "&order=newest_first"
        ),
        "brands": brands,
        "required_groups": required_groups,
        "excluded_terms": excluded_terms or EXCLUDED_TERMS,
        "limit": limit,
        "currency_code": currency_code,
        "currency": {"SEK": "kr", "DKK": "kr", "PLN": "zł", "EUR": "€"}.get(currency_code, currency_code),
        "state": Path(state),
        "size_mode": size_mode,
    }

# =========================================================
# BEFINTLIGA SÖKNINGAR – ALLA DINA 44 MARKNADER
# =========================================================
MARKETS = [
    # Ralph Lauren USA flag
    market("Ralph Lauren USA-flag tröjor Sverige", "RALPH LAUREN USA FLAG", "vinted.se",
           "Polo Ralph Lauren American flag sweater", "SEK", 400,
           ("polo ralph lauren", "ralph lauren"),
           [("sweater", "jumper", "knit", "stickad", "tröja", "pullover"),
            ("american flag", "usa flag", "flag sweater", "flag knit")],
           "seen_rl_usa_flag_se.txt"),

    # Ralph Lauren hoodies
    market("Ralph Lauren hoodies Sverige", "RALPH LAUREN", "vinted.se",
           "Polo Ralph Lauren hoodie", "SEK", 249,
           ("polo ralph lauren", "ralph lauren"),
           [("hoodie", "sweatshirt", "hooded sweatshirt")], "seen_rl_hoodie_se.txt"),
    market("Ralph Lauren hoodies Polen", "RALPH LAUREN", "vinted.pl",
           "Polo Ralph Lauren hoodie", "PLN", 60,
           ("polo ralph lauren", "ralph lauren"),
           [("hoodie", "bluza")], "seen_rl_hoodie_pl.txt"),
    market("Ralph Lauren hoodies Danmark", "RALPH LAUREN", "vinted.dk",
           "Polo Ralph Lauren hoodie", "DKK", 100,
           ("polo ralph lauren", "ralph lauren"),
           [("hoodie", "hættetrøje", "sweatshirt")], "seen_rl_hoodie_dk.txt"),

    # Ralph Lauren stickat
    market("Ralph Lauren klassiska stickade tröjor Sverige", "RALPH LAUREN", "vinted.se",
           "Polo Ralph Lauren sweater", "SEK", 199,
           ("polo ralph lauren", "ralph lauren"),
           [("sweater", "jumper", "knit", "stickad", "tröja", "pullover"),
            ("cable", "flätstickad", "quarter zip", "half zip", "polo bear", "vintage", "pony", "knitted")],
           "seen_rl_sweater_se.txt"),

    # Ralph Lauren dunjackor
    market("Ralph Lauren dunjackor Sverige", "RALPH LAUREN", "vinted.se",
           "Polo Ralph Lauren down jacket", "SEK", 849,
           ("polo ralph lauren", "ralph lauren"),
           [("puffer", "down jacket", "down coat", "dunjacka", "dun")], "seen_rl_down_se.txt"),
    market("Ralph Lauren dunjackor Polen", "RALPH LAUREN", "vinted.pl",
           "Polo Ralph Lauren puffer", "PLN", 320,
           ("polo ralph lauren", "ralph lauren"),
           [("puffer", "down jacket", "down coat", "dunjacka", "kurtka puchowa")], "seen_rl_down_pl.txt"),
    market("Ralph Lauren dunjackor Danmark", "RALPH LAUREN", "vinted.dk",
           "Polo Ralph Lauren puffer", "DKK", 535,
           ("polo ralph lauren", "ralph lauren"),
           [("puffer", "down jacket", "down coat", "dunjacka", "dunjakke")], "seen_rl_down_dk.txt"),

    # Abercrombie pälshoodies och jackor
    market("Abercrombie pälshoodies Sverige", "ABERCROMBIE & FITCH", "vinted.se",
           "Abercrombie faux fur hoodie", "SEK", 400,
           ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"),
           [("hoodie", "hooded sweatshirt", "sweatshirt"),
            ("fur", "faux fur", "fur lined", "fur-lined", "sherpa", "päls", "pälsfodrad", "fuskpäls")],
           "seen_abercrombie_fur.txt"),
    market("Abercrombie & Fitch jackor Sverige", "ABERCROMBIE & FITCH JACKA", "vinted.se",
           "Abercrombie jacket", "SEK", 450,
           ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"),
           [("jacket", "jacka", "coat", "parka", "vinterjacka", "puffer")],
           "seen_abercrombie_jackets_se.txt",
           excluded_terms=EXCLUDED_TERMS + ("vest", "väst", "gilet", "hoodie")),

    # Patagonia fleecevästar
    market("Patagonia fleecevästar Sverige", "PATAGONIA FLEECEVÄST", "vinted.se",
           "Patagonia fleece vest", "SEK", 400, ("patagonia",),
           [("vest", "väst", "fleecevest", "gilet"), ("fleece", "synchilla", "retro-x", "retro x", "pile")],
           "seen_patagonia_se.txt"),
    market("Patagonia fleecevästar Polen", "PATAGONIA FLEECEVÄST", "vinted.pl",
           "Patagonia fleece vest", "PLN", 200, ("patagonia",),
           [("vest", "gilet", "kamizelka"), ("fleece", "synchilla", "retro-x", "polar")],
           "seen_patagonia_pl.txt"),
    market("Patagonia fleecevästar Danmark", "PATAGONIA FLEECEVÄST", "vinted.dk",
           "Patagonia fleece vest", "DKK", 335, ("patagonia",),
           [("vest", "gilet"), ("fleece", "synchilla", "retro-x", "pile")],
           "seen_patagonia_dk.txt"),

    # Colmar jackor
    market("Colmar jackor Sverige", "COLMAR", "vinted.se", "Colmar jacket", "SEK", 300,
           ("colmar",), [("jacka", "jacket", "puffer", "dunjacka", "vinterjacka")], "seen_colmar_se.txt"),
    market("Colmar jackor Polen", "COLMAR", "vinted.pl", "Colmar jacket", "PLN", 100,
           ("colmar",), [("jacka", "jacket", "puffer", "kurtka", "kurtka puchowa")], "seen_colmar_pl.txt"),
    market("Colmar jackor Danmark", "COLMAR", "vinted.dk", "Colmar jacket", "DKK", 170,
           ("colmar",), [("jacka", "jacket", "puffer", "vinterjakke")], "seen_colmar_dk.txt"),

    # J.Lindeberg jackor
    market("J.Lindeberg jackor Sverige", "J.LINDEBERG", "vinted.se", "J.Lindeberg jacket", "SEK", 300,
           ("j.lindeberg", "j lindeberg", "jlindeberg"), [("jacka", "jacket", "coat", "vinterjacka")],
           "seen_jl_se.txt", excluded_terms=EXCLUDED_TERMS + ("puffer", "down jacket", "down coat", "dunjacka", "dun", "pufferjacka")),
    market("J.Lindeberg jackor Polen", "J.LINDEBERG", "vinted.pl", "J.Lindeberg jacket", "PLN", 100,
           ("j.lindeberg", "j lindeberg", "jlindeberg"), [("jacka", "jacket", "coat", "kurtka")],
           "seen_jl_pl.txt", excluded_terms=EXCLUDED_TERMS + ("puffer", "down jacket", "down coat", "dunjacka", "dun", "pufferjacka")),
    market("J.Lindeberg jackor Danmark", "J.LINDEBERG", "vinted.dk", "J.Lindeberg jacket", "DKK", 170,
           ("j.lindeberg", "j lindeberg", "jlindeberg"), [("jacka", "jacket", "coat", "vinterjakke")],
           "seen_jl_dk.txt", excluded_terms=EXCLUDED_TERMS + ("puffer", "down jacket", "down coat", "dunjacka", "dun", "pufferjacka")),

    # Skor
    market("Lanvin skor Sverige", "LANVIN SKOR", "vinted.se", "Lanvin shoes sneakers", "SEK", 700,
           ("lanvin",), [("shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers", "loafer", "boot", "boots", "sko", "skor")],
           "seen_lanvin_shoes_se.txt", size_mode="shoe"),
    market("Valentino skor Sverige", "VALENTINO SKOR", "vinted.se", "Valentino Garavani shoes sneakers", "SEK", 600,
           ("valentino", "valentino garavani"), [("shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers", "loafer", "boot", "boots", "sko", "skor")],
           "seen_valentino_shoes_se.txt", size_mode="shoe"),
    market("Maison Margiela GAT Sverige", "MAISON MARGIELA GAT", "vinted.se", "Maison Margiela GAT Replica sneakers", "SEK", 800,
           ("maison margiela", "maison martin margiela", "margiela"),
           [("gat", "german army trainer", "replica sneaker", "replica sneakers"),
            ("shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers", "sko", "skor")],
           "seen_margiela_gat_se.txt", excluded_terms=tuple(t for t in EXCLUDED_TERMS if t != "replica"), size_mode="shoe"),
    market("Adidas x Wales Bonner skor Sverige", "ADIDAS X WALES BONNER", "vinted.se", "Adidas Wales Bonner shoes sneakers", "SEK", 700,
           ("adidas", "wales bonner"),
           [("wales bonner", "walesbonner"), ("shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers", "sko", "skor")],
           "seen_adidas_wales_bonner_se.txt", size_mode="shoe"),

    # Barbour
    market("Barbour klassiska jackor Sverige", "BARBOUR", "vinted.se", "Barbour jacket", "SEK", 400,
           ("barbour",), [("jacka", "jacket", "coat"),
                           ("wax", "quilted", "bedale", "beaufort", "ashby", "liddesdale", "beadnell", "international", "classic")],
           "seen_barbour_se.txt"),

    # Hollister cardigans
    market("Hollister cardigans Sverige", "HOLLISTER CARDIGAN", "vinted.se", "Hollister cardigan", "SEK", 400,
           ("hollister",), [("cardigan", "cardigans", "kofta", "koftor")], "seen_hollister_cardigan_se.txt"),
    market("Hollister cardigans Polen", "HOLLISTER CARDIGAN", "vinted.pl", "Hollister cardigan", "PLN", 155,
           ("hollister",), [("cardigan", "cardigans", "kardigan", "kardigany")], "seen_hollister_cardigan_pl.txt"),
    market("Hollister cardigans Finland", "HOLLISTER CARDIGAN", "vinted.fi", "Hollister cardigan", "EUR", 35,
           ("hollister",), [("cardigan", "cardigans", "neuletakki")], "seen_hollister_cardigan_fi.txt"),
    market("Hollister cardigans Danmark", "HOLLISTER CARDIGAN", "vinted.dk", "Hollister cardigan", "DKK", 260,
           ("hollister",), [("cardigan", "cardigans", "strikjakke")], "seen_hollister_cardigan_dk.txt"),

    # Abercrombie cardigans
    market("Abercrombie cardigans Sverige", "ABERCROMBIE CARDIGAN", "vinted.se", "Abercrombie cardigan", "SEK", 400,
           ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"), [("cardigan", "cardigans", "kofta", "koftor")], "seen_abercrombie_cardigan_se.txt"),
    market("Abercrombie cardigans Polen", "ABERCROMBIE CARDIGAN", "vinted.pl", "Abercrombie cardigan", "PLN", 155,
           ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"), [("cardigan", "cardigans", "kardigan", "kardigany")], "seen_abercrombie_cardigan_pl.txt"),
    market("Abercrombie cardigans Finland", "ABERCROMBIE CARDIGAN", "vinted.fi", "Abercrombie cardigan", "EUR", 35,
           ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"), [("cardigan", "cardigans", "neuletakki")], "seen_abercrombie_cardigan_fi.txt"),
    market("Abercrombie cardigans Danmark", "ABERCROMBIE CARDIGAN", "vinted.dk", "Abercrombie cardigan", "DKK", 260,
           ("abercrombie & fitch", "abercrombie and fitch", "abercrombie"), [("cardigan", "cardigans", "strikjakke")], "seen_abercrombie_cardigan_dk.txt"),

    # Burberry – endast svarta skjortor
    market("Burberry svarta skjortor Sverige", "BURBERRY SVART SKJORTA", "vinted.se", "Burberry shirt", "SEK", 200,
           ("burberry",), [("shirt", "shirts", "skjorta", "skjortor"), BLACK_TERMS], "seen_burberry_shirt_se.txt"),
    market("Burberry svarta skjortor Polen", "BURBERRY SVART SKJORTA", "vinted.pl", "Burberry shirt", "PLN", 78,
           ("burberry",), [("shirt", "shirts", "koszula", "koszule"), BLACK_TERMS], "seen_burberry_shirt_pl.txt"),
    market("Burberry svarta skjortor Finland", "BURBERRY SVART SKJORTA", "vinted.fi", "Burberry shirt", "EUR", 18,
           ("burberry",), [("shirt", "shirts", "paita"), BLACK_TERMS], "seen_burberry_shirt_fi.txt"),
    market("Burberry svarta skjortor Danmark", "BURBERRY SVART SKJORTA", "vinted.dk", "Burberry shirt", "DKK", 130,
           ("burberry",), [("shirt", "shirts", "skjorte", "skjorter"), BLACK_TERMS], "seen_burberry_shirt_dk.txt"),

    # Ralph Lauren – blå och vita skjortor
    market("Ralph Lauren blå och vita skjortor Sverige", "RALPH LAUREN BLÅ/VIT SKJORTA", "vinted.se", "Polo Ralph Lauren shirt", "SEK", 149,
           ("polo ralph lauren", "ralph lauren"), [("shirt", "shirts", "skjorta", "skjortor"), BLUE_TERMS + WHITE_TERMS], "seen_rl_shirt_se.txt"),
    market("Ralph Lauren blå och vita skjortor Polen", "RALPH LAUREN BLÅ/VIT SKJORTA", "vinted.pl", "Polo Ralph Lauren shirt", "PLN", 58,
           ("polo ralph lauren", "ralph lauren"), [("shirt", "shirts", "koszula", "koszule"), BLUE_TERMS + WHITE_TERMS], "seen_rl_shirt_pl.txt"),
    market("Ralph Lauren blå och vita skjortor Finland", "RALPH LAUREN BLÅ/VIT SKJORTA", "vinted.fi", "Polo Ralph Lauren shirt", "EUR", 13,
           ("polo ralph lauren", "ralph lauren"), [("shirt", "shirts", "paita"), BLUE_TERMS + WHITE_TERMS], "seen_rl_shirt_fi.txt"),
    market("Ralph Lauren blå och vita skjortor Danmark", "RALPH LAUREN BLÅ/VIT SKJORTA", "vinted.dk", "Polo Ralph Lauren shirt", "DKK", 97,
           ("polo ralph lauren", "ralph lauren"), [("shirt", "shirts", "skjorte", "skjorter"), BLUE_TERMS + WHITE_TERMS], "seen_rl_shirt_dk.txt"),

    # Stone Island – endast stickat
    market("Stone Island stickade tröjor Sverige", "STONE ISLAND STICKAD TRÖJA", "vinted.se", "Stone Island knit sweater", "SEK", 300,
           ("stone island",), [("knit", "knitwear", "sweater", "jumper", "pullover", "stickad", "stickat", "tröja", "maglione", "sweter", "dzianin", "strik")], "seen_stone_island_knit_se.txt"),
    market("Stone Island stickade tröjor Polen", "STONE ISLAND STICKAD TRÖJA", "vinted.pl", "Stone Island knit sweater", "PLN", 100,
           ("stone island",), [("knit", "knitwear", "sweater", "jumper", "pullover", "stickad", "stickat", "tröja", "maglione", "sweter", "dzianin", "strik")], "seen_stone_island_knit_pl.txt"),
    market("Stone Island stickade tröjor Finland", "STONE ISLAND STICKAD TRÖJA", "vinted.fi", "Stone Island knit sweater", "EUR", 26,
           ("stone island",), [("knit", "knitwear", "sweater", "jumper", "pullover", "stickad", "stickat", "tröja", "maglione", "sweter", "dzianin", "neulepaita", "strik")], "seen_stone_island_knit_fi.txt"),
    market("Stone Island stickade tröjor Danmark", "STONE ISLAND STICKAD TRÖJA", "vinted.dk", "Stone Island knit sweater", "DKK", 170,
           ("stone island",), [("knit", "knitwear", "sweater", "jumper", "pullover", "stickad", "stickat", "tröja", "maglione", "sweter", "dzianin", "strik")], "seen_stone_island_knit_dk.txt"),
]

# =========================================================
# ITALIEN – EN SÖKNING PER KATEGORI, ÄVEN SKOR
# =========================================================
ITALY_SEARCHES = [
    {
        "source": "Ralph Lauren USA-flag tröjor Sverige",
        "search": "Polo Ralph Lauren maglione bandiera americana",
        "groups": [("maglione", "maglia", "pullover"), ("bandiera americana", "bandiera usa", "american flag")],
    },
    {
        "source": "Ralph Lauren hoodies Sverige",
        "search": "Polo Ralph Lauren felpa con cappuccio",
        "groups": [("felpa con cappuccio", "felpa", "hoodie")],
    },
    {
        "source": "Ralph Lauren klassiska stickade tröjor Sverige",
        "search": "Polo Ralph Lauren maglione",
        "groups": [("maglione", "maglia", "pullover", "knitwear"), ("cable", "treccia", "quarter zip", "half zip", "polo bear", "pony")],
    },
    {
        "source": "Ralph Lauren dunjackor Sverige",
        "search": "Polo Ralph Lauren piumino",
        "groups": [("piumino", "giubbotto imbottito", "giacca imbottita")],
    },
    {
        "source": "Abercrombie pälshoodies Sverige",
        "search": "Abercrombie felpa cappuccio pelliccia",
        "groups": [("felpa con cappuccio", "felpa", "hoodie"), ("pelliccia", "finta pelliccia", "sherpa", "fur")],
    },
    {
        "source": "Abercrombie & Fitch jackor Sverige",
        "search": "Abercrombie giacca",
        "groups": [("giacca", "cappotto", "parka", "jacket")],
    },
    {
        "source": "Patagonia fleecevästar Sverige",
        "search": "Patagonia gilet pile",
        "groups": [("gilet", "smanicato", "vest"), ("pile", "fleece", "synchilla", "retro-x")],
    },
    {
        "source": "Colmar jackor Sverige",
        "search": "Colmar giacca",
        "groups": [("giacca", "piumino", "giubbotto", "jacket")],
    },
    {
        "source": "J.Lindeberg jackor Sverige",
        "search": "J.Lindeberg giacca",
        "groups": [("giacca", "cappotto", "jacket")],
    },
    {
        "source": "Lanvin skor Sverige",
        "search": "Lanvin scarpe sneakers",
        "groups": [("scarpa", "scarpe", "sneaker", "sneakers", "stivali", "shoes")],
        "size_mode": "shoe",
    },
    {
        "source": "Valentino skor Sverige",
        "search": "Valentino Garavani scarpe sneakers",
        "groups": [("scarpa", "scarpe", "sneaker", "sneakers", "stivali", "shoes")],
        "size_mode": "shoe",
    },
    {
        "source": "Maison Margiela GAT Sverige",
        "search": "Maison Margiela GAT sneakers",
        "groups": [("gat", "german army trainer", "replica sneaker", "replica sneakers"), ("scarpa", "scarpe", "sneaker", "sneakers", "trainer", "shoes")],
        "size_mode": "shoe",
    },
    {
        "source": "Adidas x Wales Bonner skor Sverige",
        "search": "Adidas Wales Bonner scarpe sneakers",
        "groups": [("wales bonner", "walesbonner"), ("scarpa", "scarpe", "sneaker", "sneakers", "shoes")],
        "size_mode": "shoe",
    },
    {
        "source": "Barbour klassiska jackor Sverige",
        "search": "Barbour giacca cerata",
        "groups": [("giacca", "cappotto", "jacket"), ("cerata", "wax", "quilted", "bedale", "beaufort", "ashby")],
    },
    {
        "source": "Hollister cardigans Sverige",
        "search": "Hollister cardigan",
        "groups": [("cardigan", "maglia aperta", "giacca di maglia")],
    },
    {
        "source": "Abercrombie cardigans Sverige",
        "search": "Abercrombie cardigan",
        "groups": [("cardigan", "maglia aperta", "giacca di maglia")],
    },
    {
        "source": "Burberry svarta skjortor Sverige",
        "search": "Burberry camicia nera",
        "groups": [("camicia", "camicie", "shirt"), ("nero", "nera", "nere", "neri", "black")],
    },
    {
        "source": "Ralph Lauren blå och vita skjortor Sverige",
        "search": "Polo Ralph Lauren camicia",
        "groups": [("camicia", "camicie", "shirt"), ("blu", "azzurro", "azzurra", "navy", "bianco", "bianca", "bianche", "bianchi", "blue", "white")],
    },
    {
        "source": "Stone Island stickade tröjor Sverige",
        "search": "Stone Island maglione maglia",
        "groups": [("maglione", "maglia", "lavorato a maglia", "knitwear", "sweater", "pullover")],
    },
]


def add_italy_markets():
    italy_markets = []

    for entry in ITALY_SEARCHES:
        source = next(
            (config for config in MARKETS if config["name"] == entry["source"]),
            None,
        )
        if source is None:
            print(f"⚠️ Saknar mall för Italien: {entry['source']}")
            continue

        euro_limit = round(source["limit"] * 0.089)
        if entry["source"] == "Stone Island stickade tröjor Sverige":
            euro_limit = 27

        safe_name = re.sub(r"[^a-z0-9]+", "_", entry["source"].lower()).strip("_")
        italy_markets.append({
            "name": source["name"].replace("Sverige", "Italien"),
            "brand_header": source["brand_header"],
            "base": "https://www.vinted.it",
            "url": (
                "https://www.vinted.it/catalog?"
                f"search_text={quote(entry['search'])}"
                f"&price_to={euro_limit:.2f}&currency=EUR&order=newest_first"
            ),
            "brands": source["brands"],
            "required_groups": entry["groups"],
            "excluded_terms": source["excluded_terms"],
            "limit": euro_limit,
            "currency_code": "EUR",
            "currency": "€",
            "state": Path(f"seen_italy_{safe_name}.txt"),
            "size_mode": entry.get("size_mode", source.get("size_mode", "clothing")),
        })

    return italy_markets


MARKETS.extend(add_italy_markets())

# =========================================================
# TEXT OCH ANNONSER
# =========================================================
def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
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

    normalized = text.replace("\xa0", " ").replace("\u202f", " ").replace(",", ".")
    if currency_code in ("SEK", "DKK"):
        patterns = (
            r"(\d+(?:\.\d{1,2})?)\s*kr\.?",
            r"kr\.?\s*(\d+(?:\.\d{1,2})?)",
            r"(\d+(?:\.\d{1,2})?)\s*SEK",
        )
    elif currency_code == "PLN":
        patterns = (
            r"(\d+(?:\.\d{1,2})?)\s*zł",
            r"zł\s*(\d+(?:\.\d{1,2})?)",
            r"(\d+(?:\.\d{1,2})?)\s*PLN",
        )
    elif currency_code == "EUR":
        patterns = (
            r"€\s*(\d+(?:\.\d{1,2})?)",
            r"(\d+(?:\.\d{1,2})?)\s*€",
            r"(\d+(?:\.\d{1,2})?)\s*EUR",
        )
    else:
        return None

    for pattern in patterns:
        matches = re.findall(pattern, normalized, flags=re.IGNORECASE)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                pass
    return None


def detect_size(text, size_mode="clothing"):
    if size_mode == "shoe":
        patterns = (
            r"(?:eu|eur|size|storlek|strl|stl|taille|rozmiar|taglia)\s*[:\-]?\s*(3[5-9]|4[0-9]|50)\b",
            r"\b(3[5-9]|4[0-9]|50)\s*(?:eu|eur)\b",
        )
        for pattern in patterns:
            found = re.search(pattern, text, flags=re.IGNORECASE)
            if found:
                return found.group(1) + " EU"

        without_prices = re.sub(
            r"\b\d+(?:[.,]\d{1,2})?\s*(?:kr\.?|sek|zł|pln|dkk|eur|€)\b",
            " ", text, flags=re.IGNORECASE,
        )
        candidates = re.findall(r"(?<!\d)(3[5-9]|4[0-9]|50)(?!\d)", without_prices)
        return candidates[0] + " EU" if candidates else None

    labeled = re.search(
        r"(?:size|storlek|strl|stl|taille|rozmiar|taglia)\s*[:\-]?\s*(XL|S|M|L)\b",
        text, flags=re.IGNORECASE,
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
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=20)
        if response.status_code in (200, 204):
            print("✅ Discord-notis skickad.")
            return True
        print("❌ Discord-fel:", response.status_code, response.text[:300])
        return False
    except Exception as exc:
        print("❌ Discord exception:", exc)
        return False

# =========================================================
# VÄNTA VID HTTP 429
# =========================================================
def retry_wait(response, attempt):
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            wait_seconds = float(retry_after)
        except ValueError:
            try:
                retry_date = parsedate_to_datetime(retry_after)
                wait_seconds = (retry_date - datetime.now(timezone.utc)).total_seconds()
            except Exception:
                wait_seconds = 120 * (2 ** attempt)
    else:
        wait_seconds = 120 * (2 ** attempt)

    wait_seconds = max(1, min(wait_seconds, 900))
    print(f"⏳ HTTP 429. Väntar {int(wait_seconds)} sekunder innan nytt försök.")
    time.sleep(wait_seconds)

# =========================================================
# SKANNA EN MARKNAD
# =========================================================
def scan_market(config, global_seen):
    print(f"\n🔎 {config['name']}")
    response = None

    for attempt in range(3):
        try:
            response = requests.get(config["url"], headers=HEADERS, timeout=30)
            print(f"HTTP {response.status_code} | {config['name']} | Försök {attempt + 1}/3")
            if response.status_code == 200:
                break
            if response.status_code == 429:
                if attempt < 2:
                    retry_wait(response, attempt)
                    continue
                print(f"❌ Misslyckades efter tre försök: {config['name']}")
                return False
            print(f"❌ HTTP-fel {response.status_code}. Sökningen kunde inte kontrolleras.")
            return False
        except requests.RequestException as exc:
            print(f"⚠️ Anslutningsfel: {exc}")
            if attempt < 2:
                wait_seconds = 30 * (2 ** attempt)
                print(f"⏳ Försöker igen om {wait_seconds} sekunder.")
                time.sleep(wait_seconds)
            else:
                print("❌ Misslyckades efter tre försök.")
                return False

    if response is None or response.status_code != 200:
        return False

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        local_seen = load_seen(config["state"])
        global_seen.update(local_seen)
        links = soup.select('a[href*="/items/"]')
        processed_ids = set()
        print(f"Hittade {len(links)} möjliga annonslänkar")

        stats = {
            "Redan sedda": 0,
            "Fel varumärke": 0,
            "Fel plaggtyp/modell/färg": 0,
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
                stats["Fel plaggtyp/modell/färg"] += 1
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

            detected_size = detect_size(text, config.get("size_mode", "clothing"))
            if config.get("size_mode", "clothing") == "clothing":
                if detected_size not in SIZES:
                    stats["Storlek saknas"] += 1
                    continue
            elif detected_size is None:
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
            print("🔥 MATCH:", item["title"], "|", item["price"], "|", item["size"])

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
        return True

    except Exception as exc:
        print(f"❌ Fel i {config['name']}: {exc}")
        return False

# =========================================================
# START
# =========================================================
def main():
    print("🚀 Vinted Sniper startar...")
    print(f"Antal sökningar: {len(MARKETS)}")
    print(f"Italienska sökningar: {len(ITALY_SEARCHES)}")

    global_seen = load_seen(GLOBAL_SEEN_FILE)
    print(f"Gemensamt sparade annonser: {len(global_seen)}")
    successful = 0
    failed = 0

    for index, config in enumerate(MARKETS):
        if index > 0:
            wait_seconds = random.uniform(8, 12)
            print(f"\n⏳ Väntar {wait_seconds:.1f} sekunder innan nästa sökning...")
            time.sleep(wait_seconds)

        if scan_market(config, global_seen):
            successful += 1
        else:
            failed += 1

    save_seen(GLOBAL_SEEN_FILE, global_seen)
    print("\n" + "=" * 45)
    print("📊 SLUTRAPPORT")
    print("=" * 45)
    print(f"Totalt antal sökningar: {len(MARKETS)}")
    print(f"✅ Lyckade: {successful}")
    print(f"❌ Misslyckade: {failed}")
    if failed == 0:
        print("\n🎉 Alla sökningar kontrollerades!")
    else:
        print("\n⚠️ Alla sökningar kunde inte kontrolleras. Kontrollera felloggen ovan.")
    print("\nBevakningen avslutad.")


if __name__ == "__main__":
    main()