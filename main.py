import requests

URL = "https://www.vinted.se/catalog?search_text=ralph%20Lauren%20hoodie&price_to=150.00&currency=SEK&search_id=5246591382&order=newest_first"

try:
    response = requests.get(URL, timeout=20)

    print("HTTP-status:", response.status_code)
    print("Svarsstorlek:", len(response.text), "tecken")
    print("Sidans innehållstyp:", response.headers.get("Content-Type"))

    if response.status_code == 200:
        print("Vinted-sidan kunde hämtas!")
    else:
        print("Vinted svarade inte med en lyckad status.")

except requests.RequestException as error:
    print("Anslutningsfel:", error)