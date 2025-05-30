
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from fastapi.responses import JSONResponse
import uuid
import logging
import json
from datetime import datetime
from LocalDB import save_scan, update_scan, get_scan, get_all_scans, init_db
import asyncio
from utils import run_osint_scan, is_valid_domain

# JSON logger
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "scan_id"):
            log_record["scan_id"] = record.scan_id
        return json.dumps(log_record)

# Logger setup
logger = logging.getLogger("uvicorn")
logger.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    domain: str


@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/scan")
async def scan_domain(request: ScanRequest):
    scan_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + 'Z'

    logger.info(f"Received scan request for domain: {request.domain}", extra={"scan_id": scan_id})

    if not is_valid_domain(request.domain):
        logger.warning("Invalid domain format", extra={"scan_id": scan_id})
        return JSONResponse(status_code=400, content={"error": "Invalid domain format"})

    try:
        scan_data = {
            "scan_id": scan_id,
            "domain": request.domain,
            "created_at": created_at,
            "status": "in_progress",
            "result": None,
            "completed_at": None,
            "summary": ""
        }

        save_scan(scan_id, scan_data)

        asyncio.create_task(run_and_store_scan(request.domain, scan_id))
        return scan_data

    except Exception as e:
        logger.error(f"Exception: {e}", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
    

@app.get("/scan/all")
async def get_all_scans_endpoint():
    return get_all_scans()

@app.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str):
    scan = get_scan(scan_id)
    if not scan:
        return JSONResponse(status_code=404, content={"error": "Scan not found"})
    return scan



async def run_and_store_scan(domain: str, scan_id: str):
    try:
        data = await run_osint_scan(domain, scan_id)
        results = data["result"]
        summary = data["summary"]
        completed_at = datetime.utcnow().isoformat() + 'Z'

        update_scan(scan_id, {
            "result": results,
            "status": "completed",
            "completed_at": completed_at,
            "summary" : summary,
        })

        logger.info("Scan completed", extra={"scan_id": scan_id})

    except Exception as e:
        logger.error(f"Scan failed: {str(e)}", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        update_scan(scan_id, {
            "status": "error",
            "result": {"error": str(e)},
            "completed_at": datetime.utcnow().isoformat() + 'Z',
        })