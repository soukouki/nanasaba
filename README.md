# nanasaba

ななさばに関連するサービス群のリポジトリです。

機能
- Simutrans Extendedサーバーの運用(simutrans-serverコンテナ)
- Discordボットによるサーバー管理(managebotコンテナ)
- LLMを活用したチャット機能(スポット検索、スクリーンショット撮影など)
- VNCを利用したSimutransのスクリーンショット撮影(simutrans-vncコンテナ)
- 各種スクリプト
  - 毎時セーブ・バックアップ用スクリプト(autosave.sh)
  - 日時バックアップ・ファイル配布用サーバーへのアップロード用スクリプト(daily.sh)

## コンテナ構成

### simutrans-server

Simutrans Extendedのサーバーを実行するコンテナです。

- ヘッドレスの実行ファイルを起動しています。
- ポート13353でサーバーを公開します。
- Pak128.Britain-Exパックを使用します。

### simutrans-vnc

VNCを利用したSimutransのスクリーンショット撮影を行うコンテナです。

- ポート5901で管理用VNCサーバーを公開しています。
- ポート26524でHTTPリクエストを介してスクリーンショットを撮影するサーバーを公開しています。
  - `curl http://localhost:26524/screenshot?x=1000&y=3000&zoomlevel=1&underground=0`の形式でスクリーンショットを取得できます。
  - 撮影したスクリーンショットは`./simutrans-vnc/data/<id>.png`に保存されます。
- llmコンテナによって、必要ないタイミングではpause状態になります。

### managebot

Discordボットを通じて、利用者がSimutransサーバーを管理できるようにするコンテナです。また、それを拡張し、チャット機能も提供しています。

- 管理のためにDocker in Dockerを利用しています。

### llm

LLM（大規模言語モデル）を使用したAPIサーバーを提供するコンテナです。管理用botのチャット機能で利用されています。

- ポート49237でAPIサーバーを公開します。
  - `curl http://localhost:49237/chat -H "Content-Type: application/json" -d '{"model": "gemma-3-4b-it-qat", "input": "3000, 4000のスクリーンショットを撮って"}'`の形式でリクエストを受け付けます。
  - 出力はストリームに対応しています。
  - 利用するモデルはOpenAI Likedなものを利用してください。OpenAI, Anthropic, LM Studioなどが利用可能です。
  - モデルを選択する場合は`llm/llm.py`を修正してください。
- MCPサーバー
  - シムトランス横断検索
    - https://github.com/soukouki/scs-mcp-server
  - スポット情報の取得
    - スポットの検索・追加・修正・削除のツールを提供しています。
    - デフォルトのスポット情報は`llm/spots.yaml`に記載しています。
    - スポットの追加等が行われると、`llm/spots.json`にコピーされ、そちらを参照するようになります。
  - スクリーンショットの撮影
    - simutrans-vncコンテナにHTTPリクエストを送信し、スクリーンショットを撮影します。
    - スクリーンショットを撮影する際には、simutrans-vncコンテナをunpauseし、撮影が終わるとpauseします。
    - pause, unpauseのためにDocker in Dockerを利用しています。

## 注意事項

- 複数個所で`nanasaba1st`がハードコーディングされています。docker composeで生成されるコンテナ名に適宜変更してください。
- `nanasaba1st-body`, `nanasaba1st-saves`, セーブデータ保存用zipファイルはGit管理されていません。
- `simutrans-vnc/shell2http_1.17.0_linux_amd64.tar.gz`はGit管理されていません。別途入手して配置する必要があります。
- `nettool`はGit管理されていません。別途入手して配置する必要があります。
- `llm/.env`, `managebot/.env`ファイルはGit管理されていません。

## TODO

- `nanasaba1st`のハードコーディングをなくす
- MCPサーバーの拡充
  - スポット情報の取得の自動化
  - 混雑状況等のゲーム内データの取得
