from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from automation.models.schemas import SearchResponse, SearchItem, ErrorPayload

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/search", response_model=SearchResponse)
async def search_endpoint(request: Request, query: str = Query(..., min_length=2), top_k: int = 5):
    try:
        menu = request.app.state.app.menu
        results = await menu.search(query, k=top_k)
        items = [SearchItem(**r) for r in results]
        return SearchResponse(query=query, results=items)
    except Exception as e:
        err = ErrorPayload(source="/automation/search", message=str(e))
        return JSONResponse(status_code=500, content=err.model_dump())


@router.get("/search_raw")
async def search_endpoint_raw(request: Request, query: str = Query(..., min_length=2), top_k: int = 5):
    try:
        menu = request.app.state.app.menu
        results = await menu.search(query, k=top_k)
        return {"query": query, "results": results}
    except Exception as e:
        err = ErrorPayload(source="/automation/search_raw", message=str(e))
        return JSONResponse(status_code=500, content=err.model_dump())
