"""
リクナビNEXTから求人情報をスクレイピングする
"""

import time
from typing import Dict, List

import pandas as pd
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
        ".styles_button__slVGb.styles_middle__GPwzV.styles_primary__iQFwH.styles_searchButton__Bde1_",
    )
    button_element.click()
    time.sleep(sleep_time)


def update_page(driver: webdriver.Chrome) -> None:
    """次のページに遷移"""
    ul_element = driver.find_element(By.CSS_SELECTOR, ".styles_module__5CsjK")
    a_element = ul_element.find_elements(By.TAG_NAME, "a")[-1]
    href = a_element.get_attribute("href") or ""
    driver.get(href)
    time.sleep(sleep_time)


def collect_all_urls(driver: webdriver.Chrome) -> List[str]:
    """全ページの求人URLを収集"""
    total_num = int(
        driver.find_element(By.CSS_SELECTOR, "span.styles_bodyText__KY7__").text
    )
    total_page_num = total_num // 100 + 1

    urls: List[str] = []
    for _ in range(total_page_num):
        urls.extend(get_item_urls(driver))
        update_page(driver)
    return urls


# ================================
# データ取得処理
# ================================
def get_item_urls(driver: webdriver.Chrome) -> List[str]:
    """一覧ページから求人詳細URLを取得"""
    elements = driver.find_elements(By.CLASS_NAME, "a.styles_bigCard__pKdMA")
    return [href for i in elements if (href := i.get_attribute("href"))]


def get_company_name(driver: webdriver.Chrome) -> str:
    """企業名を取得"""
    company_name_element = driver.find_elements(By.CLASS_NAME, "styles_bodyText__KY7__")
    return company_name_element[0].text if company_name_element else "不明"


def get_info(driver: webdriver.Chrome) -> Dict[str, str]:
    """求人ページから情報を取得"""
    data = {"会社名": get_company_name(driver)}
    table_elements = driver.find_elements(
        By.CLASS_NAME, "styles_tableAboutApplication__9iz5B"
    )

    if table_elements:
        table_html = table_elements[0].get_attribute("outerHTML")
        df = pd.read_html(table_html)[0]
        data.update({i_row[0]: i_row[1] for _, i_row in df.iterrows()})
    return data
