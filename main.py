from fastapi import HTTPException,FastAPI
from starlette import status
from database import SessionLocal, engine
from services import chat
from fastapi.middleware.cors import CORSMiddleware
import models
from schema import Request

app= FastAPI()
models.Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")  
def health_check():
    return {"status": "OK"}


@app.post(
    "/v1/chat-completions",
    summary="Reservation Chat Completion",
)
async def process_query(request: Request):
    try:
        result = await chat.run_query(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
