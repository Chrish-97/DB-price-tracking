import datetime

import pandas as pd
from matplotlib import pyplot as plt
from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import argparse
import logging

logging.getLogger().setLevel(logging.INFO)

# Set up Selenium WebDriver
#options = webdriver.ChromeOptions()
#options.add_argument("--headless")
#options.add_argument("--disable-gpu")
#options.add_argument("--window-size=1920,1080")
#options.add_argument("--enable-javascript")
#driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

options = webdriver.FirefoxOptions()
#options.add_argument("-headless")
firefox_profile = FirefoxProfile()
firefox_profile.set_preference("javascript.enabled", True)
options.profile = firefox_profile
driver = webdriver.Firefox(options=options)

def append_to_data(from_price, to_price, name):
    with open(f"data/{name}.csv", 'a+') as fd:
        fd.write(f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")},{from_price},{to_price}\n")
        logging.info(f"appended from {from_price} to {to_price} to data file")

def get_price_for_url(url, name, discount = 0):
    logging.info(f"getting price from {url}")
    driver.get(url)
    time.sleep(10)
    driver.save_screenshot(f"data/{name}-screenshot.png")
    logging.info("html: " + driver.page_source)
    result = float(re.findall(r'ab(\d*,\d*)&nbsp;€', driver.page_source)[0].replace(",", "."))
    logging.info(f"price for {url} is: {result} - after discount {round(result - result * discount / 100, 2)}")
    return round(result - result * discount / 100, 2)

def update_chart(name):
    df = pd.read_csv(f"data/{name}.csv", delimiter=',', index_col=0)
    df.index = pd.to_datetime(df.index)
    plt.figure(figsize=(20, 12))
    df.plot()
    plt.xticks(rotation=45, ha='right')
    plt.locator_params(axis='x', nbins=15)
    plt.tight_layout()
    plt.savefig(f"data/{name}.png")
    logging.info(f"plot saved to {name}.png")


parser = argparse.ArgumentParser()
parser.add_argument("--to-url", type=str, required=True)
parser.add_argument("--from-url", type=str, required=True)
parser.add_argument("--name", type=str, required=True)
parser.add_argument("--discount", type=int, required=False, default=0)
args = parser.parse_args()

logging.info("start fetching data")

to_price = get_price_for_url(args.from_url, args.name, args.discount)
from_price = get_price_for_url(args.to_url, args.name, args.discount)

append_to_data(from_price, to_price, args.name)

update_chart(args.name)

logging.info("finished fetching data")

driver.quit()