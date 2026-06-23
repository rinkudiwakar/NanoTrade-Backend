import json
from fastapi import APIRouter, Depends
from app.api.deps import get_matching_engine

router = APIRouter()

@router.get("/orderbook")
async def get_orderbook(engine = Depends(get_matching_engine)):
    book_json_str = engine.get_order_book()
    return json.loads(book_json_str)
