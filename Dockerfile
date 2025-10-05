# 以下のドキュメントを参考に作成
# https://docs.astral.sh/uv/guides/integration/docker/#using-uv-in-docker
# https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile

FROM python:3.12-slim-bookworm

# パッケージのインストール
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates curl fonts-ipafont-gothic gcc git locales sudo tmux tzdata vim zsh && \
        wget unzip gnupg libnss3 libgconf-2-4 libxi6 libxrandr2 libxcomposite1 libxcursor1 \
        libasound2 libxdamage1 libxss1 libxtst6 libglib2.0-0 libgbm-dev && \
    rm -rf /var/lib/apt/lists/*

# 言語設定
RUN echo "ja_JP UTF-8" > /etc/locale.gen && \
    locale-gen ja_JP.UTF-8
ENV LANG=ja_JP.UTF-8
ENV LC_ALL=ja_JP.UTF-8
ENV TZ=Asia/Tokyo

# Chrome + ChromeDriverのインストール
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Chromeのパスを明示
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# uvのインストール
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# システムのPythonを使用する
# cf. https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_LINK_MODE=copy

WORKDIR /app

# 依存関係のインストール
# Note: プロジェクトの依存関係はソースコードに比べて変更頻度が低いので、レイヤーを分けてキャッシュを効率的に利用する
# cf. https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# プロジェクトのソースコードをインストール
COPY ./src/ /app/src/
COPY ./README.md /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen

COPY ./app/. /app/app/
# COPY ./model/. /app/model/

CMD ["streamlit", "run", "app/app.py", "--server.port", "8501"]