from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import os
from twilio.rest import Client

# Daten für die Fahrt
von = "Coburg"
nach = "Hamburg"
hinfahrt_date = "24.04.2025"
hinfahrt_time = "06:44"
heimfahrt_date = "27.04.2025"
heimfahrt_time = "17:35"

##############################################################################################################
hinfahrt_date_object = datetime.strptime(hinfahrt_date, "%d.%m.%Y")
hinfahrt_date_string = hinfahrt_date_object.strftime("%d.%m.%Y")
hinfahrt_month_year = hinfahrt_date_object.strftime("%B %Y")
hinfahrt_day = hinfahrt_date_object.day
heimfahrt_date_object = datetime.strptime(heimfahrt_date, "%d.%m.%Y")
heimfahrt_date_string = heimfahrt_date_object.strftime("%d.%m.%Y")
heimfahrt_month_year = heimfahrt_date_object.strftime("%B %Y")
heimfahrt_day = heimfahrt_date_object.day

# csv für Preistracking
current_path = os.getcwd()
CSV_FILE = os.path.join(current_path, "ticket_prices.csv")
if os.path.exists(CSV_FILE):
    # print(os.path)
    df = pd.read_csv(CSV_FILE)
    previous_hin = df.sort_values(by='Zeit', ascending=False).iloc[0]['Hin_Preis']
    previous_heim = df.sort_values(by='Zeit', ascending=False).iloc[0]['Zurück_Preis']
    # print(f"hin:{previous_hin}, heim:{previous_heim}")
    csv = True
    # print("csv ist da")
else:
    csv = False
    df = pd.DataFrame(columns=["Zeit", "Hin_Preis", "Zurück_Preis"])
    previous_hin = 1
    previous_heim = 1
    print("csv erstmalig erstellen")

# Pics für Screenshots für Beweis
screenshot_dir = os.path.join(current_path, "Bilder")
if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)
    print("Ordner für pics erstellt")

jetzt = datetime.now()
datum_uhrzeit = jetzt.strftime("%d-%m-%Y_%H-%M")
# Musste trainline nehmen, da auf DB seite Probleme hatte mit dem Cookie banner. Auf trainline kann ich den banner akzeptieren
BASE_URL = "https://www.trainline.de"


# Starte WebDriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Im Hintergrund laufen lassen
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver


# Warten und Elemente klicken
def wait_and_interact(driver, by, value, action='click', text=None):
    element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, value)))

    if action == 'click':
        element.click()
    elif action == 'send_keys':
        element.clear()
        element.send_keys(text)
        sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li[role="option"]'))
        )
        try:
            suggestions = driver.find_elements(By.CSS_SELECTOR, 'li[role="option"]')
            option_found = False
            for suggestion in suggestions:
                suggestion_text = suggestion.text
                # print(f"Vorschlagstext: {suggestion_text}")
                if text in suggestion_text:
                    suggestion.click()
                    option_found = True
                    print(f" {text} aus dropdown ausgewählt")
                    sleep(1)
                    break
            if not option_found:
                raise Exception(f"Kein passender Vorschlag für {text} gefunden")
        except:
            print("Fehler: beim  interagieren mit den Elementen")
    return element


# Wähle ein Datum aus
def choose_date(driver, target_month, target_day):
    # erst überprüfen ob in dem geöffneten Datepicker, das gewünschte Datum vorhanden ist ansonsten in den nächsten monat klicken
    while True:
        current_month = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "datetime-picker-label"))
        ).text
        if current_month == target_month:
            break
        # nächsten Monat klicken
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="calendar-navigate-to-next-month"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        driver.execute_script("arguments[0].click();", next_button)
        sleep(1)
    # Tag aus Kalender anklicken
    day_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[data-testid="jsf-calendar-date-button-{target_day}"]'))
    )
    driver.execute_script("arguments[0].click();", day_button)


# Ticket suchen und Preis extrahieren mit Screenshot der Ticketpreise
def screenshot_and_extract_journey_info(driver, screenshot_path, target_time=None):
    try:
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Günstige Tickets sichern')]"))
        )
        search_button.click()
        sleep(5)
        # Screenshot für Beweis
        driver.save_screenshot(screenshot_path)

        journey_containers = driver.find_elements(By.XPATH, "//div[contains(@data-test, 'eu-journey-row')]")
        available_journeys = []
        target_price = None
        # Liste alle gefundenen Zeiten auf und überprüfe ob gewünschte Zeit hinfart_time gefunden wird um preis zu extrahieren
        for index, container in enumerate(journey_containers):
            try:
                time_element = container.find_element(By.XPATH, ".//time")
                departure_time = time_element.text
                price_element = container.find_element(
                    By.XPATH,
                    ".//div[contains(@data-test, 'standard-ticket-price')]/span"
                )
                price = price_element.text.replace("$", "").replace(",", ".").strip()

                journey_info = {
                    "index": index,
                    "departure_time": departure_time,
                    "price": float(price)
                }
                available_journeys.append(journey_info)

                # überprüfe ob die gefundene zeit die gesuchte zeit ist
                if departure_time == target_time:
                    target_price = float(price)
                    print(f"Gesuchte Reise gefunden: Option [{index}] mit Zeit {departure_time} und Preis: {price}€")
                    break
                else:
                    continue

            except NoSuchElementException:
                # print(f"Fehler Reise {index}")
                continue

        # Rückgabe vom PReis der gesuchten Reise
        if target_price is not None:
            print(f"Ausgewählte Reise: Abfahrt {target_time}, Preis: {target_price}€")
            return target_price
        else:
            if target_time:
                print(
                    f"Keine Reise mit Abfahrtszeit {target_time} gefunden. Gewünschte Abfahrtzeit wirklich vorhanden auf DB seite?")
                raise
            return None

    except TimeoutException:
        print("Timeout: Elemente wurden nicht rechtzeitig gefunden.")
        return None
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")
        return None


# Benachrichtigungsfunktion über Twilio
def send_notification(message_body):
    # token aus Twilio
    account_sid = [account_sid_from_Twilio]
    auth_token = [auth_token_from_Twilio]
    client = Client(account_sid, auth_token)

    recipients = ["add whatsappp numbers from recipients"]

    for recipient in recipients:
        message = client.messages.create(
            body=message_body,
            from_='whatsapp:+14155238886',  # Twilio WhatsApp-Nummer
            to=recipient
        )
    print("whatsapp gesendet")


# main function für hin und rückfahrt
def book_ticket(von, nach, hinfahrt_date_object, heimfahrt_date_object):
    global df
    driver = init_driver()

    try:
        driver.get(BASE_URL)
        print("Webseite geöffnet")

        # cookies akzeptieren
        wait_and_interact(driver, By.ID, "onetrust-accept-btn-handler", 'click')

        # Von Feld ausfüllen
        wait_and_interact(driver, By.ID, "jsf-origin-input", 'send_keys', von)
        sleep(1)

        # Nach Feld ausfüllen
        wait_and_interact(driver, By.ID, "jsf-destination-input", 'send_keys', nach)
        sleep(1)

        # Datum wählen
        wait_and_interact(driver, By.ID, "jsf-outbound-time-input-toggle", 'click')
        choose_date(driver, hinfahrt_date_object.strftime("%B %Y"), hinfahrt_date_object.day)

        # Uhrzeit und Minuten auswählen
        wait_and_interact(driver, By.ID, "jsf-outbound-time-time-picker-hour", 'click')
        wait_and_interact(driver, By.XPATH, "//option[@value='05']", 'click')
        select_minute = Select(driver.find_element(By.ID, "jsf-outbound-time-time-picker"))
        select_minute.select_by_value("15")

        # Checkbox deaktivieren, die noch eine neue seite mit booking.com Unterkünften öffnen würde
        booking_checkbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "bookingPromo"))
        )
        if booking_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", booking_checkbox)
            sleep(1)

        # Ticketpreis extrahieren und Screenshot machen
        screenshot_path = os.path.join(screenshot_dir, f"{datum_uhrzeit}_hinfahrt_screenshot.png")
        extracted_price_1 = screenshot_and_extract_journey_info(driver, screenshot_path, hinfahrt_time)
        print(f"Hinfahrt Ticketpreis extracted_price_1: {extracted_price_1}")
        driver.quit()
        sleep(2)

        ######################################### Heimfahrt wiederholen #####################################
        driver = init_driver()
        driver.get(BASE_URL)
        print("Webseite geöffnet")

        # Cookie akzeptieren
        wait_and_interact(driver, By.ID, "onetrust-accept-btn-handler", 'click')

        # Von Feld ausfüllen
        wait_and_interact(driver, By.ID, "jsf-origin-input", 'send_keys', nach)
        sleep(1)

        # Nach Feld ausfüllen
        wait_and_interact(driver, By.ID, "jsf-destination-input", 'send_keys', von)
        sleep(1)

        # Datum wählen
        wait_and_interact(driver, By.ID, "jsf-outbound-time-input-toggle", 'click')
        choose_date(driver, heimfahrt_date_object.strftime("%B %Y"), heimfahrt_date_object.day)

        # Uhrzeit und Minuten auswählen
        wait_and_interact(driver, By.ID, "jsf-outbound-time-time-picker-hour", 'click')
        wait_and_interact(driver, By.XPATH, "//option[@value='17']", 'click')
        select_minute = Select(driver.find_element(By.ID, "jsf-outbound-time-time-picker"))
        select_minute.select_by_value("30")

        # Checkbox "Unterkünfte anzeigen" deaktivieren
        booking_checkbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "bookingPromo"))
        )
        if booking_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", booking_checkbox)
            sleep(1)

        # Ticketpreis extrahieren und Screenshot machen
        screenshot_path = os.path.join(screenshot_dir, f"{datum_uhrzeit}_heimfahrt_screenshot.png")
        extracted_price_2 = screenshot_and_extract_journey_info(driver, screenshot_path, heimfahrt_time)
        print(f"Heimfahrt Ticketpreis extracted_preice_2: {extracted_price_2}")

        # Preise in CSV speichern
        new_row = pd.DataFrame([{
            "Zeit": jetzt.strftime("%Y-%m-%d %H:%M:%S"),
            "Hin_Preis": extracted_price_1,
            "Zurück_Preis": extracted_price_2
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        print("Preise in CSV gespeichert")

    finally:
        driver.quit()
        # whatapp senden
        #### Text definieren#######
        if previous_hin > extracted_price_1 and previous_heim > extracted_price_2 and csv:
            value_hin = (previous_hin - extracted_price_1) / 10
            value_hin = round(value_hin, 2)
            value_heim = (previous_heim - extracted_price_2) / 10
            value_heim = round(value_heim, 2)
            body = f"""*****KOOOOOOOOOORN*****
Du kannst {value_hin} Schlachtplatten bei der Hinfahrt und {value_heim} bei der Heimfahrt sparen.
Hinfahr vorher: {previous_hin}€
Jetzt: {extracted_price_1}€
Heimfahrt vorher: {previous_heim}€
Jetzt: {extracted_price_2}€
*****KOOOOOOOOOORN*****""".strip()

        elif previous_hin > extracted_price_1 and csv:
            value_hin = (previous_hin - extracted_price_1) / 10
            value_hin = round(value_hin, 2)
            body = f"""Kniebohrer Alarm!
Du kannst {value_hin} Schlachtplatten bei der Hinfahrt sparen.
Vorheriger Preis: {previous_hin}€
Jetziger Preis: {extracted_price_1}€""".strip()

        elif previous_heim > extracted_price_2 and csv:
            value_heim = (previous_heim - extracted_price_2) / 10
            value_heim = round(value_heim, 2)
            body = f"""Kniebohrer Alarm!
Du kannst {value_heim} Schlachtplatten bei der Heimfahrt sparen. 
Vorheriger Preis: {previous_heim}€
Jetziger Preis: {extracted_price_2}€""".strip()

    if not csv:
        print("erster Eintrag in csv - Preistracking hat erst begonnen")

    elif previous_hin > extracted_price_1 or previous_heim > extracted_price_2:
        send_notification(body)
    else:
        print(f"Keine Preisänderung hin:{previous_hin}, heim:{previous_heim}")


## funktion ausführen
book_ticket(von, nach, hinfahrt_date_object, heimfahrt_date_object)
