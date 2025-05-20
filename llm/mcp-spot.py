
import json
import yaml
from fastmcp import FastMCP

mcp = FastMCP("mcp-spot")

spots = []
# spotsの構造は以下のようになっている
# [
#   {
#     "name": "政場駅",
#     "rank": 1.0,
#     "coord": {"x": 1043, "y": 3080},
#     "description": "マップの中心都市である政場市にあり、近郊列車や南西方向へ向かう特急列車が発着する。"
#   }
# ]
# rankは0.0から1.0の値を持ち、1.0が最も重要なスポットを示す。
# 検索結果が多い場合は、rankが高い順に並べ、下位のスポットは省略する。

try:
    with open("spots.json", "r") as f:
        spots = json.load(f)
except FileNotFoundError:
    with open("spots.yaml", "r") as f:
        spots = yaml.safe_load(f)

# 同じ名前のスポットをマージする関数
def merge_same_spot(spots):
    merged_spots = []
    seen_names = set()

    for spot in spots:
        name = spot["name"]
        if name not in seen_names:
            seen_names.add(name)
            merged_spots.append(spot)
        else:
            # 既に存在するスポットとマージ
            existing_spot = next(s for s in merged_spots if s["name"] == name)
            existing_spot["rank"] = max(existing_spot["rank"], spot["rank"])
            # x, y座標は最後のスポットのものを優先
            existing_spot["coord"]["x"] = spot["coord"]["x"]
            existing_spot["coord"]["y"] = spot["coord"]["y"]
            existing_spot["description"] += " " + spot["description"]

    return merged_spots

@mcp.tool()
async def search_spot(name: str) -> str:
    """
    Simutransというゲームのスポット(役所・駅・空港など)を検索し、説明と座標を返す。
    """
    if name == "":
        return "スポット名を指定してください。"

    # 同じ名前のスポットがある場合
    # rankの高い順に並べ、表示
    matches = sorted(
        [spot for spot in spots if spot["name"] == name],
        key=lambda x: x["rank"],
        reverse=True,
    )
    matches = merge_same_spot(matches)
    if len(matches) > 0:
        # name, coord, descriptionを返す
        return json.dumps([{"name": spot["name"], "coord": spot["coord"], "description": spot["description"]} for spot in matches], ensure_ascii=False)

    # 部分一致するスポットを検索
    # rankの高い順に並べ、10件まで表示
    matches = sorted(
        [spot for spot in spots if name in spot["name"]],
        key=lambda x: x["rank"],
        reverse=True,
    )[:10]
    matches = merge_same_spot(matches)
    if len(matches) > 0:
        return json.dumps([{"name": spot["name"], "coord": spot["coord"], "description": spot["description"]} for spot in matches], ensure_ascii=False)

    # 文章検索
    # rankの高い順に並べ、10件まで表示
    matches = sorted(
        [spot for spot in spots if name in spot["description"]],
        key=lambda x: x["rank"],
        reverse=True,
    )[:10]
    matches = merge_same_spot(matches)
    if len(matches) > 0:
        # マッチした文字列の前後のみを表示
        # 例: "政場市にあり、近郊列車や南西方向へ向かう特急列車が発着する。"のなかで「特急列車」がマッチした場合
        # => {"name": "政場駅", "coord": {"x": 1043, "y": 3080}, "match": "南西方向へ向かう「特急列車」が発着する。"}
        result = []
        for spot in matches:
            description = spot["description"]
            start = max(description.find(name) - 10, 0)
            end = min(description.find(name) + len(name) + 10, len(description))
            match = description[start:end]
            result.append({"name": spot["name"], "coord": spot["coord"], "match": match})
        return json.dumps(result, ensure_ascii=False)

    # マッチしなかった場合
    return "スポットが見つかりませんでした。部分文字列など、もう少し広い範囲で検索してみてください。"

@mcp.tool()
def create_spot(name: str, x: int, y: int, description: str) -> str:
    """
    Simutransというゲームのスポット(役所・駅・空港など)を登録する。

    name: スポット名
    x: スポットのx座標
    y: スポットのy座標
    description: スポットの説明文
    """
    if name == "":
        return "スポット名を指定してください。"
    if x < 0 or y < 0:
        return "座標は正の整数で指定してください。"
    if description == "":
        return "説明文を指定してください。"

    # spots.jsonに追加
    new_spot = {
        "name": name,
        "rank": 0.2, # ユーザーが登録したスポットはrankを下げる
        "coord": {"x": x, "y": y},
        "description": description,
    }
    spots.append(new_spot)
    with open("spots.json", "w") as f:
        json.dump(spots, f, ensure_ascii=False)

    return f"{name}を登録しました。"

@mcp.tool()
def update_spot(name: str, x: int, y: int, description: str) -> str:
    """
    Simutransというゲームのスポット(役所・駅・空港など)を修正する。

    name: スポット名
    x: 新しいx座標
    y: 新しいy座標
    description: 新しい説明文
    """
    if name == "":
        return "スポット名を指定してください。"
    if x < 0 or y < 0:
        return "座標は正の整数で指定してください。"
    if description == "":
        return "説明文を指定してください。"

    # spots.jsonを修正
    for spot in spots:
        if spot["name"] == name:
            spot["coord"] = {"x": x, "y": y}
            spot["description"] = description
            break
    else:
        return f"{name}は登録されていません。"

    with open("spots.json", "w") as f:
        json.dump(spots, f, ensure_ascii=False)

    return f"{name}を修正しました。"

@mcp.tool()
def delete_spot(name: str) -> str:
    """
    Simutransというゲームのスポット(役所・駅・空港など)を削除する。
    """
    if name == "":
        return "スポット名を指定してください。"

    log = ""
    # spots.jsonを修正
    for spot in spots:
        if spot["name"] != name:
            continue
        if spot["rank"] > 0.21:
            log += f"{name}はユーザーが登録したスポットではないため、削除できません。\n"
        spots.remove(spot)
        log += f"{name}を削除しました。\n"
        break
    else:
        return f"{name}は登録されていません。"

    with open("spots.json", "w") as f:
        json.dump(spots, f, ensure_ascii=False)

    return log

if __name__ == "__main__":
    mcp.run()
