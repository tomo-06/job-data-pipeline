# tests/test_job_scraper.py
from unittest.mock import patch

import pandas as pd

from job_data_pipeline.job_scraper import (
    get_company_name,
    get_info,
    get_item_urls,
    search_jobs,
    update_page,
)


# ================================
# SeleniumのWebElementの代替
# ================================
class DummyElement:
    def __init__(self, href: str | None = None) -> None:
        self.text = ""
        self.clicked = False
        self.href = href or ""
        self.sub_elements: list["DummyElement"] = []

    def send_keys(self, word: str) -> None:
        self.text = word

    def click(self) -> None:
        self.clicked = True

    def get_attribute(self, name: str) -> str:
        # href属性を含む場合はその値を返す
        if name == "href":
            return self.href
        return ""

    def find_element(self, by: str, value: str) -> "DummyElement":
        # 検索欄を探す場合は自分自身を返す（連鎖対応） search_jobsで使用
        return self

    def find_elements(self, by: str, value: str) -> list["DummyElement"]:
        # ページネーションのリンク要素のリストを返す update_pageで使用
        return self.sub_elements


# ================================
# Seleniumのwebdriver.Chromeの代替
# ================================
class DummyDriver:
    def __init__(self) -> None:
        self.visited_url = ""
        self.input_element = DummyElement()

        # ページネーション用モック
        self.pagination_element = DummyElement()
        self.pagination_element.sub_elements = [
            DummyElement("https://next.rikunabi.com/page1"),
            DummyElement("https://next.rikunabi.com/page2"),
            DummyElement("https://next.rikunabi.com/page3"),
        ]
        # 求人カードリスク用モック
        self.item_elements = [
            DummyElement("https://next.rikunabi.com/datai1"),
            DummyElement("https://next.rikunabi.com/datai2"),
            DummyElement("https://next.rikunabi.com/datai3"),
        ]
        # 企業名要素リスト用モック
        self.company_name_elements = [
            DummyElement(),
        ]
        self.company_name_elements[0].text = "株式会社テストカンパニー"

        # 求人詳細テーブル用モック
        self.table_elements = [DummyElement()]
        self.table_elements[0].get_attribute = (
            lambda name: "<table><tr><td>勤務地</td><td>東京都千代田区</td></tr></table>"
        )

    def get(self, url: str) -> None:
        self.visited_url = url

    def find_element(self, by: str, value: str) -> DummyElement:
        # ページネーションを探して、pagination_element を返す
        if "pagination" in value or "styles_module__5CsjK" in value:
            return self.pagination_element
        # "rnn-header__search__inner" が来たら input_element を返す
        return self.input_element

    def find_elements(self, by: str, value: str) -> list[DummyElement]:
        # get_item_urls用の要素リストを返す
        if "styles_bigCard__pKdMA" in value:
            return self.item_elements
        # get_company_name用の要素リストを返す
        if "styles_bodyText__KY7__" in value:
            return self.company_name_elements
        # get_info用の要素リストを返す
        if "styles_tableAboutApplication__9iz5B" in value:
            return self.table_elements
        return []


# ================================
# テストケース
# ================================
def test_search_jobs_with_mock() -> None:
    """search_jobs() のモックテスト"""
    dummy_driver = DummyDriver()
    search_jobs(driver=dummy_driver, search_word="データアナリスト")

    assert dummy_driver.visited_url.startswith("https://next.rikunabi.com/")
    assert dummy_driver.input_element.text == "データアナリスト"


def test_update_page_with_mock() -> None:
    """update_page() のモックテスト"""
    dummy_driver = DummyDriver()
    update_page(dummy_driver)
    assert dummy_driver.visited_url == "https://next.rikunabi.com/page3"


def test_get_item_urls_with_mock() -> None:
    """get_item_urls() のモックテスト"""
    dummy_driver = DummyDriver()
    urls = get_item_urls(dummy_driver)

    assert len(urls) == 3
    assert urls[0] == "https://next.rikunabi.com/datai1"
    assert urls[-1] == "https://next.rikunabi.com/datai3"


def test_get_company_name_with_mock() -> None:
    """get_company_name() のモックテスト"""
    dummy_driver = DummyDriver()
    company_name = get_company_name(dummy_driver)

    assert company_name == "株式会社テストカンパニー"


def test_get_info_with_mock() -> None:
    """get_info() のモックテスト"""
    dummy_driver = DummyDriver()

    mock_df = pd.DataFrame(
        {
            0: ["勤務地", "給与", "勤務時間"],
            1: ["東京都千代田区", "月給30万円~", "9:00~18:00"],
        }
    )

    with patch("pandas.read_html", return_value=[mock_df]):
        data = get_info(dummy_driver)

    assert data["会社名"] == "株式会社テストカンパニー"
    assert data["勤務地"] == "東京都千代田区"
    assert data["給与"] == "月給30万円~"
    assert data["勤務時間"] == "9:00~18:00"
