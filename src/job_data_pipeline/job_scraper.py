"""
リクナビNEXTから求人情報をスクレイピングする
"""

import csv
import re
import time
from typing import Dict, List

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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

    try:
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
    except Exception as e:
        print(f"[ERROR] 検索処理でエラー発生: {e}")


def update_page(driver: webdriver.Chrome) -> None:
    """次のページに遷移"""
    try:
        ul_element = driver.find_element(By.CSS_SELECTOR, ".styles_module__5CsjK")
        a_element = ul_element.find_elements(By.TAG_NAME, "a")[-1]
        href = a_element.get_attribute("href") or ""
        driver.get(href)
        time.sleep(sleep_time)
    except Exception as e:
        print(f"[ERROR] 次ページ遷移に失敗しました: {e}")


def collect_all_urls(driver: webdriver.Chrome) -> List[str]:
    """全ページの求人URLを収集"""
    try:
        element = (
            driver.find_element(By.CLASS_NAME, "styles_headerCard__BdI1Z")
            .find_element(By.TAG_NAME, "span")
            .text
        )
    except NoSuchElementException:
        print("[ERROR] 求人件数の要素が見つかりません。")
        return []

    if "以上" in element:
        total_num = int("".join(filter(str.isdigit, element)))
    else:
        match = re.search(r"〜\s*(\d+)", element)
        total_num = int(match.group(1)) if match else 0

    total_page_num = total_num // 100 + 1
    urls: List[str] = []

    for page in range(total_page_num):
        print(f"[INFO] {page + 1}/{total_page_num}ページ目を取得中...")
        urls.extend(get_item_urls(driver))
        if page + 1 < total_page_num:
            update_page(driver)

    print(f"[INFO] 全URL収集完了: {len(urls)}件")
    return urls


# ================================
# データ取得処理
# ================================
def get_item_urls(driver: webdriver.Chrome) -> List[str]:
    """一覧ページから求人詳細URLを取得"""
    try:
        elements = driver.find_elements(By.CLASS_NAME, "styles_bigCard__pKdMA")
        return [href for i in elements if (href := i.get_attribute("href"))]
    except Exception as e:
        print(f"[WARN] URL取得に失敗: {e}")
        return []


def get_company_name(driver: webdriver.Chrome) -> str:
    """企業名を取得（待機＋例外対応）"""
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[class*='styles_company']")
            )
        )
        name_tag = element.find_element(By.TAG_NAME, "p")
        return name_tag.text.strip() if name_tag else "不明"
    except (NoSuchElementException, TimeoutException):
        return "不明"
    except Exception as e:
        print(f"[WARN] 企業名取得に失敗: {e}")
        return "不明"


def get_info(driver: webdriver.Chrome) -> Dict[str, str]:
    """求人ページから情報を取得"""
    data = {"会社名": get_company_name(driver)}

    try:
        table_elements = driver.find_elements(
            By.CLASS_NAME, "styles_tableAboutApplication__9iz5B"
        )
        if table_elements:
            table_html = table_elements[0].get_attribute("outerHTML")
            df = pd.read_html(table_html)[0]
            data.update({i_row[0]: i_row[1] for _, i_row in df.iterrows()})
    except Exception as e:
        print(f"[WARN] 求人詳細情報の取得失敗: {e}")
    return data


def scrape_details(
    driver: webdriver.Chrome, project_urls: List[str]
) -> List[Dict[str, str]]:
    """求人詳細ページをスクレイピング"""
    results: List[Dict[str, str]] = []
    for i, i_url in enumerate(project_urls, 1):
        try:
            driver.get(i_url)
            time.sleep(sleep_time)
            info = get_info(driver)
            results.append(info)
            print(f"[INFO] {i}/{len(project_urls)} 件目完了: {info.get('会社名')}")
        except Exception as e:
            print(f"[WARN] {i}/{len(project_urls)} 件目でエラー発生: {e}")
            results.append({"会社名": "不明"})
            continue
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
    df = run_scraping("データスチュワード")
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
