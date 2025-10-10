from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Request
from automation.models.schemas import WSMessage, ErrorPayload

router = APIRouter(tags=["automation"])


@router.websocket("/automation/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_json()
            text = msg.get("text", "")

            # Access long-lived deps
            app_state = getattr(websocket.app.state, "app", None)
            if app_state is None:
                await websocket.send_json(ErrorPayload(source="ws", message="app state missing").model_dump())
                continue
            llm = app_state.llm
            menu = app_state.menu

            intent = await llm.classify_intent(text)
            if intent.get("type") == "search":
                res = await menu.search(intent.get("query", text), k=5)
                await websocket.send_json(
                    WSMessage(event="search_results", data={"query": text, "results": res}, llm_source=intent.get("source")).model_dump()
                )
            else:
                await websocket.send_json(
                    WSMessage(event="info", data={"message": "unsupported intent"}, llm_source=intent.get("source")).model_dump()
                )
    except WebSocketDisconnect:
        return
    except Exception as e:
        await websocket.send_json(ErrorPayload(source="ws", message=str(e)).model_dump())


from pydantic import BaseModel
from automation.core.session_manager import get_session_manager

class OrchestrationRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

@router.post("/automation/orchestrate")
async def orchestrate_intent(request: Request, payload: OrchestrationRequest):
    """HTTP alternative to WebSocket for intent orchestration with session context"""
    try:
        text = payload.text
        session_id = payload.session_id
        
        # Get or create session
        session_mgr = get_session_manager()
        session = session_mgr.get_or_create_session(session_id)
        
        # Access long-lived deps (same as WS)
        app_state = getattr(request.app.state, "app", None)
        if app_state is None:
            return ErrorPayload(source="orchestrate", message="app state missing").model_dump()
        
        llm = app_state.llm
        menu = app_state.menu
        
        # Enhanced intent classification with session context
        intent = await llm.classify_intent(text)
        
        # Handle different intent types
        if intent.get("type") == "search":
            res = await menu.search(intent.get("query", text), k=5)
            response = WSMessage(
                event="search_results", 
                data={"query": text, "results": res, "session_id": session.session_id}, 
                llm_source=intent.get("source")
            ).model_dump()
        elif intent.get("type") == "order":
            # Basic order handling - can be expanded
            response = WSMessage(
                event="order_intent", 
                data={
                    "message": "Order processing not yet implemented", 
                    "session_id": session.session_id,
                    "last_results": session.last_results or []
                }, 
                llm_source=intent.get("source")
            ).model_dump()
        else:
            response = WSMessage(
                event="info", 
                data={"message": "I can help you search for menu items. Try asking about pizza, burgers, or salads!", "session_id": session.session_id}, 
                llm_source=intent.get("source")
            ).model_dump()
        
        # Update session with this exchange
        session.add_exchange(text, intent, response)
        
        return response
            
    except Exception as e:
        return ErrorPayload(source="orchestrate", message=str(e)).model_dump()


@router.get("/automation/sessions/stats")
async def session_stats():
    """Get session manager statistics"""
    session_mgr = get_session_manager()
    return session_mgr.get_session_info()
