from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.schemas.chat import QueryRequest
from app.common.AI.chatbot import app_graph, get_session_history
from langchain_core.messages import HumanMessage, AIMessage
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)

@router.get("/chat")
async def chatbot(request: Request):
    query = request.query_params.get("query")
    if not query:
        return StreamingResponse(iter(["No query provided."]), media_type="text/plain")

    async def response_generator(session_id="1"):
        try:
            config = {"configurable": {"session_id": session_id}}
            human_input = query
            session_history = get_session_history(session_id)
            session_history.add_message(HumanMessage(content=human_input))
            initial_state = {"messages": session_history.messages}

            async for event in app_graph.astream_events({"messages": initial_state["messages"]}, version="v2", config=config):
                kind = event["event"]
                tags = event.get("tags", [])
                if kind == "on_chat_model_stream" and "final_node" in tags:
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"data: {content}\n\n"  

            yield "data: end\n\n"

        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")
