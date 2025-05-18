#!/bin/bash

# Remove any stale X lock files
rm -f /tmp/.X99-lock

# Start virtual framebuffer on display :99
Xvfb :99 -screen 0 3840x2160x16 &
sleep 2

# /simutrans-roの各データを/simutransにコピーする
# ただし/simutrans-ro/saveはコピーしない
rsync -a --exclude='save' /simutrans-ro/ /simutrans/
# /simutrans-ro/saveの各ファイルへのシンボリックリンクを作成する
mkdir -p /simutrans/save
for file in /simutrans-ro/save/*; do
  filename=$(basename "$file")
  ln -s "$file" "/simutrans/save/$filename"
done

# Launch simutrans
# restart it if it exits
cp /simutrans-ro/server13353-network.sve /simutrans/save/latest.sve
/simutrans/simutrans-extended -fullscreen -nosound -nomidi -pause -load "latest" -debug 2 &
PID=$!
while true; do
  if ! ps -p $PID > /dev/null; then
    echo "Simutrans process has exited. Restarting..."
    cp /simutrans-ro/server13353-network.sve /simutrans/save/latest.sve
    /simutrans/simutrans-extended -fullscreen -nosound -nomidi -pause -load "latest" -debug 2 &
    PID=$!
  fi
  sleep 5
done &

# Give it time to fully initialize
sleep 2

# screenshot server on background
shell2http -port 8080 -form /screenshot "DISPLAY=$DISPLAY /app/screenshot.sh \$v_x \$v_y \$v_zoomlevel \$v_underground" &

# Start VNC server exposing :99
x11vnc -display :99 -forever -rfbauth /root/.vnc/passwd -quiet -listen 0.0.0.0 -xkb
