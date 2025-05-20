#!/usr/bin/env bash
set -e

x=$1
y=$2
zoomlevel=$3
underground=$4

# 画面中央にカーソルを移動
xdotool mousemove 1920 1080

sleep 0.05

# zoomlevelが0なら3回マウスホイールup
# zoomlevelが1なら何もしない
# zoomlevelが2なら3回マウスホイールdown
# zoomlevelが3なら6回マウスホイールdown
if [ "$zoomlevel" -eq 0 ]; then
    xdotool click --repeat=3 4
elif [ "$zoomlevel" -eq 2 ]; then
    xdotool click --repeat=3 5
elif [ "$zoomlevel" -eq 3 ]; then
    xdotool click --repeat=6 5
fi

# 地下モードのときはShift+uを押す
if [ "$underground" -eq 1 ]; then
    xdotool key Shift+u
fi

sleep 0.05

# キー入力
xdotool key Shift+j
sleep 0.05
xdotool type --delay 30 "$x,$y"
sleep 0.05
xdotool key Return
sleep 0.05
xdotool key Escape

sleep 0.2

# スクリーンショット取得
id="$(date +%Y-%m-%d_%H-%M-%S)"
outfile="/app/data/${id}.png"
scrot "$outfile"

sleep 0.05

# ズームを元に戻す
if [ "$zoomlevel" -eq 0 ]; then
    xdotool click --repeat=3 5
elif [ "$zoomlevel" -eq 2 ]; then
    xdotool click --repeat=3 4
elif [ "$zoomlevel" -eq 3 ]; then
    xdotool click --repeat=6 4
fi

# 地下モードを元に戻す
if [ "$underground" -eq 1 ]; then
    xdotool key Shift+u
fi

sleep 0.1

# 出力
echo "{\"x\":$x,\"y\":$y,\"id\":\"$id\",\"zoomlevel\":$zoomlevel,\"underground\":$underground}"
