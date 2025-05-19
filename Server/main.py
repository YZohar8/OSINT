from fastapi import FastAPI, Request
from pydantic import BaseModel
import uuid
import logging
import json

app = FastAPI()

# Logging setup with JSON formatter
logger = logging.getLogger("uvicorn")
handler = logging.StreamHandler()
formatter = logging.Formatter(json.dumps({
    "level": "%(levelname)s",
    "scan_id": "%(scan_id)s",
    "message": "%(message)s"
}))
handler.setFormatter(formatter)
logger.handlers = [handler]
logger.setLevel(logging.INFO)

class ScanRequest(BaseModel):
    domain: str

@app.post("/scan")
async def scan_domain(request: ScanRequest):
    scan_id = str(uuid.uuid4())
    log_message = f"Received scan request for domain: {request.domain}"
    logger.info(log_message, extra={"scan_id": scan_id})
    return {"scan_id": scan_id, "message": "i got you"}
