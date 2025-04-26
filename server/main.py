from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running"}

# Placeholder endpoint for plugin to call
@app.post("/consult")
async def consult(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    file_content = data.get("file_content", "")
    # Basic echo logic for demonstration
    return JSONResponse(content={
        "status": "ok",
        "received_prompt": prompt,
        "received_file_content_preview": file_content[:200]  # preview first 200 chars
    })
