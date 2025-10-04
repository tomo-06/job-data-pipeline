# tests/test_job_scraper.py
from job_data_pipeline.job_scraper import search_jobs, update_page


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
        self.pagination_element = DummyElement()
        self.pagination_element.sub_elements = [
            DummyElement("https://next.rikunabi.com/page1"),
            DummyElement("https://next.rikunabi.com/page2"),
            DummyElement("https://next.rikunabi.com/page3"),
        ]

    def get(self, url: str) -> None:
        self.visited_url = url

    def find_element(self, by: str, value: str) -> DummyElement:
        # ページネーションを探して、pagination_element を返す
        if "pagination" in value or "styles_module__5CsjK" in value:
            return self.pagination_element
        # "rnn-header__search__inner" が来たら input_element を返す
        return self.input_element


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
