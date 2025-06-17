import json
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import random

base_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(base_dir, "logs", "bump_log.txt")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

DELAY_MINUTES = [0, 4, 8, 12, 16, 20, 24]

def log(message):
    timestamp = time.strftime("[%H:%M:%S] ")
    full = timestamp + message
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full + "\n")
    print(full)

def create_driver():
    options = Options()
    options.headless = True
    try:
        driver = webdriver.Firefox(options=options)
    except Exception as e:
        log(f"❌ Erreur lancement Firefox : {e}")
        raise e
    return driver

def login_discord(driver, email, password):
    try:
        driver.get("https://discord.com/login")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'email'))).send_keys(email)
        driver.find_element(By.NAME, 'password').send_keys(password)
        driver.find_element(By.NAME, 'password').send_keys(Keys.RETURN)
        WebDriverWait(driver, 60).until(EC.url_contains("channels"))
        log(f"✅ Connecté à Discord : {email}")
    except Exception as e:
        log(f"❌ Erreur connexion {email} : {e}")
        raise e

def bump_channel(driver, server_id, channel_id, email):
    try:
        url = f"https://discord.com/channels/{server_id}/{channel_id}"
        driver.get(url)
        log(f"⏳ Tentative bump : {email} → {server_id}/{channel_id}")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))).click()
        time.sleep(1)
        driver.switch_to.active_element.send_keys("/bump")
        time.sleep(1)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(1)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(3)
        log(f"✅ Bump réussi : {email} → {server_id}/{channel_id}")
    except Exception as e:
        log(f"⚠️ Erreur bump {email} sur {server_id}/{channel_id} : {e}")

def bump_loop(account, index):
    delay = DELAY_MINUTES[index] * 60
    time.sleep(delay)
    server_index = 0

    while True:
        try:
            driver = create_driver()
            login_discord(driver, account["email"], account["password"])
            server = account["servers"][server_index]
            bump_channel(driver, server[0], server[1], account["email"])
            driver.quit()
        except Exception as e:
            log(f"🚨 Échec pour {account['email']} : {e}")
        server_index = (server_index + 1) % len(account["servers"])
        time.sleep(1800)

def main():
    config_path = os.path.join(base_dir, "credentials.json")
    if not os.path.exists(config_path):
        log("❌ credentials.json introuvable.")
        return

    with open(config_path) as f:
        accounts = json.load(f)

    for i, acc in enumerate(accounts):
        if acc.get("enabled", True):
            threading.Thread(target=bump_loop, args=(acc, i), daemon=True).start()

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    log("🚀 SlyBump lancé")
    main()
