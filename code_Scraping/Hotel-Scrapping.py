import csv
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === Configuration ===
CITIES = [
    "Tunis", "Monastir", "Djerba", "Cairo", "Casablanca",
    "Paris", "London", "Rome", "Nice", "Barcelona", "Madrid"
]

VALID_PROVIDERS = [
    "Booking.com", "Expedia", "Agoda.com", "Priceline", "Opodo", "KAYAK",
    "Hotels.com", "HotelTonight", "Travelocity", "Orbitz"
]

# === Setup ChromeDriver for Linux VM ===
options = Options()
options.binary_location = "/usr/bin/chromium-browser"   # Adjust if necessary
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--blink-settings=imagesEnabled=false')
options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 30)

all_data = []
all_providers = set()

# === Logging Function ===
def log(message):
    print(message, flush=True)
    with open("scraping_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

# === Price Extraction ===
def extract_all_prices(card_scope):
    prices = {}
    top_offers = card_scope.find_elements(By.CSS_SELECTOR, "div.qSC7 a.hzpu")
    for offer in top_offers:
        try:
            provider = offer.find_element(By.CSS_SELECTOR, "img.afsH").get_attribute("alt").strip()
            price = offer.find_element(By.CSS_SELECTOR, "div.Ptt7-price").text.strip()
            if provider in VALID_PROVIDERS and price:
                prices[provider] = price
                all_providers.add(provider)
        except:
            continue
    detailed_offers = card_scope.find_elements(By.CSS_SELECTOR, "div.zV27-price-container")
    for offer in detailed_offers:
        try:
            provider = offer.find_element(By.CSS_SELECTOR, "img.afsH").get_attribute("alt").strip()
            price_elem = offer.find_elements(By.CSS_SELECTOR, "div.c1XBO")
            price = price_elem[0].text.strip() if price_elem else ""
            if provider in VALID_PROVIDERS and price:
                prices[provider] = price
                all_providers.add(provider)
        except:
            continue
    return prices

# === Hotel Details Extraction ===
def scrape_hotel_details(hotel_link):
    stars = ""
    description = ""
    driver.execute_script(f"window.open('{hotel_link}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.hEI8")))
        stars_elem = driver.find_elements(By.CSS_SELECTOR, "span.hEI8")
        stars = stars_elem[0].text.strip() if stars_elem else ""
        desc_elem = driver.find_elements(By.CSS_SELECTOR, "div.b40a-desc-text")
        description = desc_elem[0].text.strip().replace("\n", " ") if desc_elem else ""
    except:
        pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return stars, description

# === Main Loop: 4 Months x Cities ===
start_date = datetime.today()
days_to_scrape = 30 * 4  # Approx. 4 months

for day_offset in range(days_to_scrape):
    checkin = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
    checkout = (start_date + timedelta(days=day_offset + 1)).strftime("%Y-%m-%d")

    for city in CITIES:
        log(f"[{checkin}] Scraping {city}...")

        kayak_city = city.replace(" ", "%20")
        url = f"https://www.kayak.ae/hotels/{kayak_city}-c/{checkin}/{checkout}/2adults"
        driver.get(url)

        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            cookie_btn.click()
        except:
            pass

        while True:
            time.sleep(3)
            hotel_cards = driver.find_elements(By.CSS_SELECTOR, "div.S0Ps-resultInner")

            for card in hotel_cards:
                try:
                    name_elem = card.find_element(By.CSS_SELECTOR, "a.c9Hnq-big-name")
                    name = name_elem.text.strip()
                    hotel_link = name_elem.get_attribute("href")
                    location_elem = card.find_elements(By.CSS_SELECTOR, "div.upS4-big-name")
                    location = location_elem[0].text.strip() if location_elem else ""
                    rating = card.find_element(By.CSS_SELECTOR, ".Dp6Q").text.strip() if card.find_elements(By.CSS_SELECTOR, ".Dp6Q") else ""
                    review_raw = card.find_element(By.CSS_SELECTOR, ".DOkx-rating-review-score").text.strip() if card.find_elements(By.CSS_SELECTOR, ".DOkx-rating-review-score") else ""
                    reviews = review_raw.replace(rating, '').strip() if rating and review_raw else review_raw
                    prices = extract_all_prices(card)
                    try:
                        dropdown_btn = card.find_element(By.CSS_SELECTOR, "button[aria-label*='more sites']")
                        driver.execute_script("arguments[0].click();", dropdown_btn)
                        time.sleep(2)
                        prices.update(extract_all_prices(card))
                    except:
                        pass
                    stars, description = scrape_hotel_details(hotel_link)
                    row = {
                        "Checkin_Date": checkin,
                        "City": city,
                        "Name": name,
                        "Location": location,
                        "Rating": rating,
                        "Reviews": reviews,
                        "Stars": stars,
                        "Description": description
                    }
                    for provider, price in prices.items():
                        row[provider] = price
                    all_data.append(row)
                except:
                    continue

            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next page']")
                if next_btn.get_attribute("aria-disabled") == "true":
                    break
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(5)
            except:
                break

        log(f"[{checkin}] Finished {city}.\n")
        time.sleep(5)

# === Export Single CSV ===
all_providers_sorted = sorted(all_providers)
fieldnames = ["Checkin_Date", "City", "Name", "Location", "Rating", "Reviews", "Stars", "Description"] + all_providers_sorted

with open("hotels_data_4months.csv", "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in all_data:
        for provider in all_providers_sorted:
            if provider not in row:
                row[provider] = ""
        writer.writerow(row)

driver.quit()
log(f"🎉 Scraping complete! Data saved to hotels_data_4months.csv\n")
