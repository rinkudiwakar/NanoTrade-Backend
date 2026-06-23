import json
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.api.deps import get_matching_engine

router = APIRouter()

@router.get("/orderbook")
async def get_orderbook(engine = Depends(get_matching_engine)):
    try:
        book_json_str = engine.get_order_book()
        parsed_orderbook = json.loads(book_json_str)
        
        # Unscale matching engine quantities from integers (10^6 units) to floats (BTC)
        if isinstance(parsed_orderbook, dict):
            for side_name in ["bids", "asks"]:
                if side_name in parsed_orderbook:
                    for entry in parsed_orderbook[side_name]:
                        if "quantity" in entry:
                            entry["quantity"] = entry["quantity"] / 1_000_000
                            
        return parsed_orderbook
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to get orderbook: {str(e)}", "code": "ORDERBOOK_FETCH_FAILED"}
        )
