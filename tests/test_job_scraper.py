# tests/test_job_scraper.py
from job_data_pipeline.job_scraper import search_jobs


# ================================
# SeleniumのWebElementの代替
# ================================
class DummyElement:
    text: str
    clicked: bool

    def __init__(self) -> None:
        self.text = ""
        self.clicked = False

    def send_keys(self, word: str) -> None:
        self.text = word

    def click(self) -> None:
        self.clicked = True

    def find_element(self, by: str, value: str) -> "DummyElement":
        # 検索欄を探す場合は自分自身を返す（連鎖対応）
        return self


# ================================
# Seleniumのwebdriver.Chromeの代替
# ================================
class DummyDriver:
    visited_url: str
    input_element: DummyElement

    def __init__(self) -> None:
        self.visited_url = ""
        self.input_element = DummyElement()

    def get(self, url: str) -> None:
        self.visited_url = url

    def find_element(self, by: str, value: str) -> DummyElement:
        # "rnn-header__search__inner" が来たら input_element を返す
        return self.input_element


def test_search_jobs_with_mock() -> None:
    """search_jobs() のモックテスト"""
    dummy_driver = DummyDriver()
    search_jobs(driver=dummy_driver, search_word="データアナリスト")

    assert dummy_driver.visited_url.startswith("https://next.rikunabi.com/")
    assert dummy_driver.input_element.text == "データアナリスト"
