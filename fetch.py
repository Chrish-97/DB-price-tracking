from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=chrome")  # Ensure it's using Chrome's newer headless mode
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--enable-javascript")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=options)
driver.get("https://www.whatismybrowser.com/")  # This can help check your browser settings

script_result = driver.execute_script("return navigator.userAgent;")
print("User-Agent:", script_result)

script_test = driver.execute_script("return 2 + 2;")
print("JavaScript Execution Result:", script_test)  # Should print 4 if JS works

driver.quit()