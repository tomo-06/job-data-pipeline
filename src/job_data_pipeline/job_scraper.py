"""
リクナビNEXTから求人情報をスクレイピングする
"""

import time
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ================================
# 定数設定
# ================================
sleep_time = 3
csv_name = "../data/rikunabi.csv"
url = "https://next.rikunabi.com/"


# ================================
# Chrome初期化
# ================================
def init_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=ja")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# ================================
# ページ遷移処理
# ================================
def search_jobs(driver: webdriver.Chrome, search_word: str) -> None:
    """検索ワードを入力して検索実行"""
    driver.get(url)
    time.sleep(sleep_time)

    input_element = driver.find_element(
        By.CLASS_NAME, "styles_selectedOptions__3YT3_"
    ).find_element(By.TAG_NAME, "input")
    input_element.send_keys(search_word)
    button_element = driver.find_element(
        By.CSS_SELECTOR,
        "styles_button__slVGb.styles_middle__GPwzV.styles_primary__iQFwH.styles_searchButton__Bde1_",
    )
    button_element.click()
    time.sleep(sleep_time)


def update_page(driver: webdriver.Chrome) -> None:
    """次のページに遷移"""
    ul_element = driver.find_element(By.CSS_SELECTOR, ".styles_module__5CsjK")
    a_element = ul_element.find_elements(By.TAG_NAME, "a")[-1]
    driver.get(a_element.get_attribute("href"))
    time.sleep(sleep_time)


# ================================
# データ取得処理
# ================================
def get_item_urls(driver: webdriver.Chrome) -> List[str]:
    """一覧ページから求人詳細URLを取得"""
    elements = driver.find_elements(By.CLASS_NAME, "styles_bigCard__pKdMA")
    return [i.get_attribute("href") for i in elements]
