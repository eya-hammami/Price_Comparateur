import csv
import os
import time
import sys
from datetime import datetime, timedelta
from itertools import product
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

LOG_FILE = "scraping_log.txt"

def log_message(message):
    """Logs a message to both the terminal and a log file."""
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(message + "\n")
    print(message)

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    service.log_path = os.devnull
    return webdriver.Chrome(service=service, options=options)

def scrape_kayak_flights(url):
    driver = initialize_driver()
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    flights = []

    try:
        url_parts = url.split("/")
        departure_date = url_parts[5].split("?")[0]
    except IndexError:
        departure_date = "N/A"

    while True:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'nrc6')]")))
        except Exception as e:
            log_message(f"Error waiting for flight results: {e}")
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        flight_cards = soup.find_all("div", class_="nrc6")

        for card in flight_cards:
            try:
                times = card.find("div", class_="vmXl vmXl-mod-variant-large")
                departure, arrival = times.text.split(" – ") if times else ("N/A", "N/A")

                airports = card.find_all("div", class_="c_cgF c_cgF-mod-variant-full-airport-wide")
                origin = airports[0].get_text(separator=" ") if len(airports) > 0 else "N/A"
                destination = airports[1].get_text(separator=" ") if len(airports) > 1 else "N/A"

                duration_block = card.find("div", class_="xdW8 xdW8-mod-full-airport")
                duration_div = duration_block.find("div", class_="vmXl vmXl-mod-variant-default") if duration_block else None
                flight_duration = duration_div.text.strip() if duration_div else "N/A"

                stop_span = card.find("span", class_="JWEO-stops-text")
                stop_info = stop_span.text.strip() if stop_span else "N/A"

                price = card.find("div", class_="f8F1-price-text")
                flight_price = price.text.strip() if price else "N/A"

                airline_logos = card.find_all("div", class_="c5iUd-leg-carrier")
                airline_names = [logo.find("img")["alt"] for logo in airline_logos if logo.find("img")]
                airline_names = ", ".join(airline_names) if airline_names else "N/A"

                flights.append({
                    "Departure Time": departure,
                    "Arrival Time": arrival,
                    "Origin": origin,
                    "Destination": destination,
                    "Duration": flight_duration,
                    "Stops": stop_info,
                    "Price": flight_price,
                    "Airline": airline_names,
                    "Departure Date": departure_date,
                })

            except Exception as e:
                log_message(f"Error extracting flight details: {e}")

        try:
            show_more_button = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'show-more-button')]")
            if show_more_button.is_displayed():
                show_more_button.click()
                time.sleep(5)
            else:
                break
        except Exception as e:
            log_message(f"No more 'Show more results' button or error: {e}")
            break

    driver.quit()
    return flights

def save_flights_to_csv(flights, filename="flights_data.csv"):
    if not flights:
        log_message("No flight data found to save.")
        return

    keys = flights[0].keys()
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(flights)

    log_message(f"Flight data saved to {filename}")

locations = ["TUN", "MIR", "DJE", "CAI", "CMN", "PAR", "LON", "ROM", "NCE", "BCN", "MAD"]
start_date = datetime.strptime("2025-04-04", "%Y-%m-%d")
all_flights = []


with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("Flight Scraping Log\n===================\n")

for origin, destination in product(locations, repeat=2):
    if origin == destination:
        continue
    for day_offset in range(365):
        date_str = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        url = f"https://www.kayak.ae/flights/{origin}-{destination}/{date_str}?sort=bestflight_a"
        log_message(f"Scraping: {origin} → {destination} on {date_str}")
        flights = scrape_kayak_flights(url)
        all_flights.extend(flights)

if all_flights:
    save_flights_to_csv(all_flights)
else:
    log_message("No flight data found for any search.")
