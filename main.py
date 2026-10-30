
import requests

URL = "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=150.00&currency=SEK&order=newest_first"

headers = {
    "User-Agent": "VintedSniper/0.1",
    "Accept": "text/html"
}

try:
    response = requests.get(
        URL,
        headers=headers,
        timeout=20
    )

    print("HTTP-status:", response.status_code)
    print("Svarsstorlek:", len(response.text))
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Server:", response.headers.get("Server"))
    print("Svar från Vinted:")
    print(response.text[:500])

    if response.status_code == 200:
        print("Vinted-sidan kunde hämtas!")
    elif response.status_code == 403:
        print("Vinted nekar fortfarande åtkomst.")
    else:
        print("Vinted svarade med en annan status.")

except requests.RequestException as error:
    print("Anslutningsfel:", error)
