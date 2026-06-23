from fastapi.testclient import TestClient
from fastapi_server import app
import json

client = TestClient(app)

resp = client.post('/process', json={"order_id":1,"type":"BUY","price":100.5,"quantity":10,"timestamp":1620000000})
print('STATUS', resp.status_code)
print('BODY', resp.json())
