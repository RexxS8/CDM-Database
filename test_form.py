from fastapi import FastAPI, Form
from fastapi.testclient import TestClient

app = FastAPI()

@app.post("/test")
def test(tag_ids: list[str] = Form([])):
    return {"tag_ids": tag_ids}

client = TestClient(app)
res = client.post("/test", data={"tag_ids": ["1", "Pelita Waisak"]})
print(res.json())
