from fastapi import FastAPI, Request, HTTPException
import subprocess
import json
import os

app = FastAPI()

NANOTRADE_BINARY = os.path.join(os.path.dirname(__file__), '..', 'build', 'NanoTrade.exe')

@app.post('/process')
async def process_orders(request: Request):
    try:
        payload = await request.json()
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {ex}")

    if not os.path.exists(NANOTRADE_BINARY):
        raise HTTPException(status_code=500, detail=f"NanoTrade binary not found at {NANOTRADE_BINARY}")

    # call the NanoTrade executable via stdin
    try:
        proc = subprocess.run([NANOTRADE_BINARY], input=json.dumps(payload).encode('utf-8'), capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="NanoTrade timed out")

    if proc.returncode != 0:
        # include stderr for debugging
        raise HTTPException(status_code=500, detail=proc.stderr.decode('utf-8'))

    try:
        out = json.loads(proc.stdout.decode('utf-8'))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to parse engine output: {ex}")

    return out

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
