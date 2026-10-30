
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=150.00&currency=SEK&order=newest_first"

headers = {
    "User-Agent": "VintedSniper/0.1",
    "Accept": "text/html"
}

response = requests.get(URL, headers=headers, timeout=20)
print("HTTP-status:", response.status_code)

if response.status_code != 200:
    print("Kunde inte hämta annonserna.")
    raise SystemExit

soup = BeautifulSoup(response.text, "html.parser")

found = set()

for link in soup.find_all("a", href=True):
    href = link["href"]

    if "/items/" not in href:
        continue

    full_url = urljoin("https://www.vinted.se", href)
    title = link.get_text(" ", strip=True)

    if full_url in found:
        continue

    found.add(full_url)

    print("\nANNONS")
    print("Titel:", title or "Ingen titel hittades")
    print("Länk:", full_url)

print("\nAntal unika annonslänkar:", len(found))
