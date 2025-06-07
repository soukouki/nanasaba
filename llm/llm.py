
import os
import json
import textwrap
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

app = FastAPI()

# claudeの場合
# BASE_URL = "https://api.anthropic.com/v1/"
# MODEL_NAME = 'claude-3-5-haiku-latest' # まぁまぁ(1呼び出し2円程度)
# MODEL_NAME = "claude-sonnet-4-0" # たかい(1呼び出し8-10円程度)
# API_KEY = os.getenv("ANTHROPIC_API_KEY")

# LM Studioの場合
BASE_URL = "http://host.docker.internal:1235/v1" # LM Studio
# MODEL_NAME = "gemma-3-27b-it-qat" # そこそこ
MODEL_NAME = "phi-4" # 出力フォーマットが安定しない(単にJSONを書くだけではうまく動かない)が、それをカバーできれば結構強い
API_KEY = "dummy" # LM StudioはAPIキー不要

DEFAULT_SYSTEM_PROMPT = textwrap.dedent("""
あなたはSimutransというゲームに関するエージェントです。
最後の出力には<result>タグをつけてください。

## 例1

入力 : 〇〇駅の様子を教えてください

考え方 : まずはスポットを検索し、駅がどの座標にあるのかを調べます。その後、スクリーンショットを撮ります。座標はsearch_spotの結果から取得します。必ず先にスポットを検索してからスクリーンショットを撮ってください。

出力 :
<result>
{{"message":"〇〇駅の様子です","images":["画像のID1","画像のID2"]}}
</result>

## 例2

入力 : ななさばとは何ですか？

出力 :
<result>
{{"message":"ななさばとは、sou7が運営しているSimutrans Extendedのマルチプレイサーバーです。","images":[]}}
</result>

## 例3

入力 : 七彩国の中心都市はどこですか？

考え方 : まずは中心都市を検索します。政場市が出てきたら、その座標を使ってスクリーンショットを撮ります。

出力 :
<result>
{{"message":"七彩国の中心都市は政場市です。\\n以下にスクリーンショットを載せます。","images":["政場市の画像のID"]}}
</result>

## 例4

入力 : 政場市にある駅を教えてください

考え方 : 政場市にある駅を検索します。政場市の座標を使って、スポットを検索します。リストの中から駅のみを抽出します。余計なバス停や市役所などを除外します。具体的には、スポットの名前が「駅」で終わるもののみを選びます。絶対にこの選別の手順を入れてください。その後、それぞれの駅の座標を使ってスクリーンショットを撮ります。

出力 :
<result>
{{"message":"政場市にある駅を列挙します。\\n1. 政場駅\\n2. 政場北駅\\n3. 政場東駅\\n4.政場西駅","images":["政場駅の画像のID","政場北駅の画像のID","政場東駅の画像のID","政場西駅の画像のID"]}}
</result>

## 例5

スポットの削除をしてください

出力 :
<result>
{{"message":"スポットを削除するには、スポットの名前が必要です。名前を教えてください","images":[]}}
</result>
""")

async def get_mcp_client() -> MultiServerMCPClient:
    client = MultiServerMCPClient(
        connections={
            "screenshot": {
                "command": "python",
                "args": ["./mcp-screenshot.py"],
                "transport": "stdio",
            },
            "spot": {
                "command": "python",
                "args": ["./mcp-spot.py"],
                "transport": "stdio",
            },
            "cross-search": {
                "command": "npx",
                "args": ["ts-node", "/scs-mcp-server/src/index.ts"],
                "transport": "stdio",
            },
        }
    )
    return client

@app.post("/chat")
async def chat_endpoint(request: Request):
    # Parse request JSON
    body = await request.json()
    user_input = body.get("input")

    print(f"User input: {user_input}")
    print(f"Model name: {MODEL_NAME}")
    # Initialize streaming model
    model = ChatOpenAI(
        base_url=BASE_URL,
        model_name=MODEL_NAME,
        api_key=API_KEY,
        stream_usage=True,
    )

    # Initialize tools and agent
    client = await get_mcp_client()
    tools = await client.get_tools()
    agent = create_react_agent(model, tools)

    # Build the prompt chain
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", DEFAULT_SYSTEM_PROMPT),
            ("user", "{input}"),
        ]
    )
    chain = prompt | agent

    def response_dump(responses):
        result = []
        for response in responses:
            if isinstance(response, SystemMessage):
                pass
            elif isinstance(response, HumanMessage):
                result.append({"type": "human", "content": response.content})
            elif isinstance(response, AIMessage):
                if response.content != "":
                    result.append({"type": "ai", "content": response.content})
                # tool_callsがある場合は、tool_callsを含める
                if response.tool_calls is not None:
                    for tool_call in response.tool_calls:
                        result.append({"type": "tool_call", "name": tool_call["name"], "args": tool_call["args"]})
            elif isinstance(response, ToolMessage):
                result.append({"type": "tool", "content": response.content})
        return result

    async def event_stream():
        is_first = True
        last_responses = None
        # Stream and transform events to NDJSON
        async for event in chain.astream_events({"input": user_input}):
            etype = event.get("event")
            if etype == "on_chat_model_stream":
                if is_first:
                    # Skip the first event
                    is_first = False
                    yield json.dumps({"type": "start"}) + "\n"
                chunk = event["data"]["chunk"].content
                if chunk != "":
                    yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
            elif etype == "on_tool_start":
                yield json.dumps({"type": "tool_start", "name": event.get("name")}) + "\n"
            elif etype == "on_tool_end":
                yield json.dumps({"type": "tool_end", "name": event.get("name")}) + "\n"
            elif etype == "on_chain_end":
                output = event.get("data", {}).get("output", {})
                if "messages" in output:
                    last_responses = output["messages"]
        # Final result event
        if last_responses is None:
            raise HTTPException(status_code=500, detail="No response from the model.")
        yield json.dumps({"type": "result", "messages": response_dump(last_responses)}) + "\n"
        yield json.dumps({"type": "end"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
