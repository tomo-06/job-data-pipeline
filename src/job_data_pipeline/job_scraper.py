"""
リクナビNEXTから求人情報をスクレイピングする
"""

import csv
import re
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
url = "https://next.rikunabi.com/"


# ================================
# Chrome初期化
# ================================
def init_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=ja")
    chrome_options.add_argument("--headless=new")

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
    element = (
        driver.find_element(By.CLASS_NAME, "styles_headerCard__BdI1Z")
        .find_element(By.TAG_NAME, "span")
        .text
    )
    if "以上" in element:
        total_num = int("".join(filter(str.isdigit, element)))
    else:
        match = re.search(r"〜\s*(\d+)", element)
        if match:
            total_num = int(match.group(1))
        else:
            print("Error: 想定外の形式のため、ページ数を取得できません。")
            total_num = 0

    total_page_num = total_num // 100 + 1

    urls: List[str] = []
    for _ in range(total_page_num):
        urls.extend(get_item_urls(driver))
        if total_page_num == 1:
            break
        update_page(driver)
    return urls


# ================================
# データ取得処理
# ================================
def get_item_urls(driver: webdriver.Chrome) -> List[str]:
    """一覧ページから求人詳細URLを取得"""
    elements = driver.find_elements(By.CLASS_NAME, "styles_bigCard__pKdMA")
    return [href for i in elements if (href := i.get_attribute("href"))]


def get_company_name(driver: webdriver.Chrome) -> str:
    """企業名を取得"""
    company_name_element = driver.find_element(
        By.CLASS_NAME, "styles_company___2dC_"
    ).find_element(By.TAG_NAME, "p")
    return company_name_element.text if company_name_element else "不明"


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


def scrape_details(
    driver: webdriver.Chrome, project_urls: List[str]
) -> List[Dict[str, str]]:
    """求人詳細ページをスクレイピング"""
    results: List[Dict[str, str]] = []
    for i_url in project_urls:
        driver.get(i_url)
        time.sleep(sleep_time)
        results.append(get_info(driver))
    return results


# ================================
# メイン処理
# ================================
def run_scraping(search_word: str) -> pd.DataFrame:
    """検索ワードを指定してスクレイピング全体を実行"""
    driver = init_driver()
    try:
        search_jobs(driver, search_word)
        project_urls = collect_all_urls(driver)
        resuts = scrape_details(driver, project_urls)
        df = pd.DataFrame(resuts)
        return df
    finally:
        driver.quit()


# ================================
# 単体実行用
# ================================
if __name__ == "__main__":
    df = run_scraping("データサイエンティスト")
    csv_name = "/app/data/rikunabi.csv"
    df.to_csv(
        csv_name,
        quoting=csv.QUOTE_ALL,
        escapechar='"',
        encoding="utf-8",
        lineterminator="\n",
        index=False,
    )
    print("Scraping completed!:", csv_name)
