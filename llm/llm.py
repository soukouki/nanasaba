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

# Constants for LM Studio
BASE_URL = "http://host.docker.internal:1234/v1"
DEFAULT_SYSTEM_PROMPT = textwrap.dedent("""
あなたはSimutransというゲームに関するエージェントです。
「〇〇駅(や役場や空港など)の様子を教えて」という質問に対しては、駅を検索して座標を取得し、座標を確認してからスクリーンショットを撮影してください。
出力は以下の形式で行ってください。

{{"message":"〇〇駅の様子です","images":["画像のID1","画像のID2"]}}

{{"message":"ななさばとは、sou7が運営しているSimutrans Extendedのマルチプレイサーバーです。","images":[]}}

{{"message":"七彩国の中心都市は政場市です。","images":["政場市の画像のID"]}}

{{"message":"政場市にある駅を列挙します。\n1. 政場駅\n2. 政場北駅\n3. 政場東駅","images":[]}}
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
            # 「観光名所」で検索してというと、横断検索の方を呼び出してしまうため
            # "cross-search": {
            #     "command": "npx",
            #     "args": ["ts-node", "/scs-mcp-server/src/index.ts"],
            #     "transport": "stdio",
            # },
        }
    )
    return client

@app.post("/chat")
async def chat_endpoint(request: Request):
    # Parse request JSON
    body = await request.json()
    model_name = body.get("model")
    user_input = body.get("input")

    if not model_name or not user_input:
        raise HTTPException(status_code=400, detail="`model` and `input` are required fields.")

    # Initialize streaming model
    model = ChatOpenAI(
        base_url=BASE_URL,
        model_name=model_name,
        api_key="dummy",
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
