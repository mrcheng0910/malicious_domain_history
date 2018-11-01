#encoding: utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
#chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--no-sandbox")

chromedriver = "/usr/bin/chromedriver"
os.environ["webdriver.chrome.driver"] = chromedriver
driver = webdriver.Chrome(chrome_options=chrome_options,executable_path=chromedriver)
#driver = webdriver.Chrome(executable_path=chromedriver)
driver.get("https://stackoverflow.com")
print driver.page_source
driver.save_screenshot('screen.png')
driver.quit()