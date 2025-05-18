FROM ubuntu:24.04

# VNC関連のパッケージをインストール
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      tzdata dbus \
      xvfb x11vnc \
 && rm -rf /var/lib/apt/lists/*

# Setup VNC password
RUN mkdir -p /root/.vnc \
 && x11vnc -storepasswd eritn9gg /root/.vnc/passwd

# Set display environment
ENV DISPLAY=:99

# Simutrans関連のパッケージをインストール
RUN apt-get update \
	&& apt-get install -y autoconf build-essential curl libbz2-dev libpng-dev libz-dev subversion unzip sed wget miniupnpc libsdl2-dev

# shell2httpのインストール
COPY shell2http_1.17.0_linux_amd64.tar.gz /tmp/shell2http.tar.gz
RUN tar -xzf /tmp/shell2http.tar.gz -C /usr/local/bin \
  && rm /tmp/shell2http.tar.gz \
  && chmod +x /usr/local/bin/shell2http

# その他
RUN apt-get update \
  && apt-get install -y rsync scrot xdotool
