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

# RubyとBundler、Gemのインストール
RUN apt-get update && apt-get install -y ruby-full && \
    gem install discordrb
