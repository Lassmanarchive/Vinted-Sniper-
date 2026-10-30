
import requests
from bs4 import BeautifulSoup

URL = "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=150.00&currency=SEK&order=newest_first"

headers = {
    "User-Agent": "VintedSniper/0.1",
    "Accept": "text/html"
}

response = requests.get(URL, headers=headers, timeout=20)
print("HTTP-status:", response.status_code)

if response.status_code != 200:
    print("Kunde inte hämta sidan.")
    raise SystemExit

soup = BeautifulSoup(response.text, "html.parser")
links = soup.select('a[href*="/items/"]')

print("Hittade annonslänkar:", len(links))

for number, link in enumerate(links[:5], start=1):
    print(f"\n--- ANNONS {number} ---")
    print("Länk:", link.get("href"))
    print("Länktext:", link.get_text(" ", strip=True))
    print("Aria-label:", link.get("aria-label"))

    for img in link.find_all("img"):
        print("Bildtext:", img.get("alt"))

    parent = link
    for level in range(1, 4):
        parent = parent.parent
        if parent:
            print(f"Föräldernivå {level}:",
                  parent.get_text(" ", strip=True)[:500])
