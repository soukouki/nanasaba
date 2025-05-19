FROM ubuntu:24.04

# Docker in Dockerをするための設定
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg && \
    rm -rf /var/lib/apt/lists/*

# Docker公式GPGキーを追加
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg

# Dockerリポジトリを追加
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Dockerのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Pythonのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# venvの作成
RUN python3 -m venv /venv

# パスを通す（このレイヤーだけでOKなら次行でも良い）
ENV PATH="/venv/bin:$PATH"

# Pythonの依存関係ファイルを追加
COPY requirements.txt .
# 依存関係のインストール
RUN pip install --no-cache-dir -qU -r requirements.txt

# npxのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 必要なシステムパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# シムトラ横断検索ツールのインストール
RUN git clone https://github.com/128na/scs-mcp-server.git --depth 1
RUN cd scs-mcp-server && \
    npm install