import pandas as pd
import pytest

from job_data_pipeline.transform import clean_company_name


@pytest.mark.parametrize(
    "input_name, expected",
    [
        # 全角スペース　→　半角
        ("テスト　株式会社", "テスト 株式会社"),
        # ノイズ削除
        ("テスト株式会社 東京支店", "テスト株式会社"),
        ("テスト 本店", "テスト "),
        ("株式会社テスト大阪", "株式会社テスト"),
        # 省略表記の正規化（半角）
        ("(株)テスト", "株式会社テスト"),
        ("(有)テスト", "有限会社テスト"),
        ("テスト(株)", "テスト株式会社"),
        ("テスト(有)", "テスト有限会社"),
        # 省略表記の正規化（全角）
        ("（株）テスト", "株式会社テスト"),
        ("（有）テスト", "有限会社テスト"),
        ("テスト（株）", "テスト株式会社"),
        ("テスト（有）", "テスト有限会社"),
        # 欠損値
        (pd.NA, "不明"),
    ],
)
def test_clean_company_name(input_name: str, expected: str) -> None:
    """clean_company_name関数のテスト"""
    assert clean_company_name(input_name) == expected
