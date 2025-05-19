
import fcntl
import requests
import subprocess

from fastmcp import FastMCP

mcp = FastMCP("mcp-screenshot")

@mcp.tool()
async def スクリーンショットの撮影(x: int, y: int, zoomlevel: int = 1, underground: bool = False) -> str:
    """
    Simutransというゲームのスクリーンショットを撮影する。

    x, y: スクリーンショットを撮影する座標
    zoomlevelは以下のように指定する:
    - 0: ズームイン
    - 1: 標準
    - 2: ズームアウト(弱め)
    - 3: ズームアウト(強め)
    underground: 地下を撮影する場合はTrueを指定する
    """
    url = f"http://simutrans-vnc:8080/screenshot"
    params = {'x': x, 'y': y, 'zoomlevel': zoomlevel, 'underground': 1 if underground else 0}

    lockfile = "./mcp-screenshot.lock"
    with open(lockfile, "a") as file:
        # ロックを取得
        fcntl.flock(file, fcntl.LOCK_EX)

        # dockerコンテナのpauseを解除
        try:
            subprocess.run(["docker", "unpause", "nanasaba1st-simutrans-vnc-1"], check=True)
        except subprocess.CalledProcessError:
            pass

        # 実行
        response = requests.get(url, params=params)

        # dockerコンテナのpauseを再度かける
        try:
            subprocess.run(["docker", "pause", "nanasaba1st-simutrans-vnc-1"], check=True)
        except subprocess.CalledProcessError:
            pass

        # ロックを解放
        fcntl.flock(file, fcntl.LOCK_UN)

    response.raise_for_status()  # エラー時に例外を投げる

    return response.content

if __name__ == "__main__":
    mcp.run()
