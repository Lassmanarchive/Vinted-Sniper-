
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

URL = "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=150.00&currency=SEK&order=newest_first"

headers = {
    "User-Agent": "VintedSniper/0.1",
    "Accept": "text/html"
}

response = requests.get(URL, headers=headers, timeout=20)
print("HTTP-status:", response.status_code)

if response.status_code != 200:
    raise SystemExit("Kunde inte hämta sidan.")

soup = BeautifulSoup(response.text, "html.parser")
seen = set()
count = 0

allowed_sizes = {"S", "M", "L", "XL"}

for link in soup.select('a[href*="/items/"]'):
    href = link.get("href", "")

    if href in seen:
        continue
    seen.add(href)

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

    size_match = re.search(r'(?<![A-Z])(XL|XXL|XS|S|M|L)(?![A-Z])',
                           title.upper())

    if not size_match:
        continue

    size = size_match.group(1)

    if size not in allowed_sizes:
        continue

    if "ralph lauren" not in title.lower():
        continue

    if "hoodie" not in href.lower():
        continue

    if price > 150:
        continue

    count += 1
    print("\n--- FYND ---")
    print("Titel:", title)
    print("Storlek:", size)
    print("Pris:", price, "kr")
    print("Länk:", urljoin("https://www.vinted.se", href))

print("\nAntal fynd i S–XL:", count)
