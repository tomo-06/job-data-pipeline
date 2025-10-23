"""
リクナビNEXTからスクレイピングした求人情報をクレンジング・変換する
"""

import re

import pandas as pd

# ================================
# 処理実装時に使用するデータ
# ================================
df = pd.read_csv("/app/data/rikunabi.csv")


def clean_company_name(name: str) -> str:
    """企業名のクレンジング処理
    -  全角スペースを半角に変換
    -  本店・支店・東京・大阪などのノイズを削除
    -  省略表記の正規化（(株) → 株式会社）
    """
    if pd.isna(name):
        return name

    # 全角スペースを半角に変換
    name = name.replace("　", " ")

    # ノイズ削除
    name = re.sub(r"(本店|支店|東京|大阪)", "", name)

    # 省略表記の正規化
    name = re.sub(r"\(株\)", "株式会社", name)
    name = re.sub(r"\(有\)", "有限会社", name)
    name = re.sub(r"\（株\）", "株式会社", name)
    name = re.sub(r"\（有\）", "有限会社", name)

    return name
