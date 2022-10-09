from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


keywords = input("請輸入關鍵字: ")

prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options = Options()
chrome_options.add_argument('--headless')  
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('log-level=3')
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)

browser.get("https://shopping.pchome.com.tw/")

search_input = browser.find_element(By.CLASS_NAME,"l-header__siteSearchInput")

search_input.send_keys(Keys.ENTER,keywords)

btn = browser.find_element(By.CLASS_NAME,"l-header__siteSearchBtn")
btn.click()

time.sleep(1.5)
html = browser.execute_script("return document.getElementsByTagName('body')[0].innerHTML")
soup = BeautifulSoup(html,"lxml")

print("搜尋結果: "+browser.current_url)
for tag in soup.find_all('h5',class_='prod_name'):
    for ele in tag.find_all('a',href=True):
      print("\n商品名稱: "+ele.text,"\n商品連結: https:"+ele.get('href'))

input("等待使用者...按任意鍵...關閉視窗...")