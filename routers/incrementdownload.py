from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class IncrementResponse(BaseModel):
    downloads: int

@router.post("/incrementdownload", response_model=IncrementResponse)
async def increment_download(request: Request):
    app = request.app
    app.state.download_count += 1
    return {"downloads": app.state.download_count}
