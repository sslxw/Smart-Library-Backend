from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import QueryRequest
from app.common.AI.chatbot import app_graph, get_session_history
from langchain_core.messages import HumanMessage

router = APIRouter()

@router.post("/chat")
async def chatbot(request: QueryRequest):
    async def response_generator(session_id="1"):
        config = {"configurable": {"session_id": session_id}}
        human_input = request.query
        session_history = get_session_history(session_id)
        session_history.add_message(HumanMessage(content=human_input))
        initial_state = {"messages": session_history.messages}
        
        # Invoke the graph
        graph_response = app_graph.invoke(initial_state, config=config)
        final_messages = graph_response["messages"]

        for message in final_messages:
            if not isinstance(message, HumanMessage):
                yield message.content + " "

    return StreamingResponse(response_generator(), media_type="text/plain")
