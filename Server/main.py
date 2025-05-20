from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from fastapi.responses import JSONResponse
import uuid
import logging
import json
from utils import run_osint_scan

# 👨‍🔧 Custom JSON logger that includes scan_id if provided
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "scan_id"):
            log_record["scan_id"] = record.scan_id
        return json.dumps(log_record)

# ✅ Set up the logger only once
logger = logging.getLogger("uvicorn")
logger.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 🌐 FastAPI app instance
app = FastAPI()

# 🔐 Enable CORS for the frontend
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Request model
class ScanRequest(BaseModel):
    domain: str

# 🚀 POST /scan endpoint
@app.post("/scan")
async def scan_domain(request: ScanRequest):
    scan_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    logger.info(f"Received scan request for domain: {request.domain}", extra={"scan_id": scan_id})

    # Initialize scan data
    scan_data = {
        "domain": request.domain,
        "created_at": created_at,
        "status": "in_progress",
        "result": None,
        "completed_at": None,
    }
    scan_results[scan_id] = scan_data

    # Run the scan in background
    asyncio.create_task(run_and_store_scan(request.domain, scan_id))

    logger.info("Scan task started in background", extra={"scan_id": scan_id})
    return {"scan_id": scan_id, "created_at": created_at, "status": "in_progress"}


async def run_and_store_scan(domain: str, scan_id: str):
    try:
        logger.info(f"Running tools for scan_id: {scan_id}", extra={"scan_id": scan_id})
        results = await run_osint_scan(domain, scan_id)
        completed_at = datetime.utcnow().isoformat()

        scan_results[scan_id].update({
            "result": results,
            "status": "completed",
            "completed_at": completed_at,
        })

        logger.info(f"Scan completed successfully", extra={"scan_id": scan_id})
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}", extra={"scan_id": scan_id})
        scan_results[scan_id].update({
            "status": "error",
            "result": {"error": str(e)},
            "completed_at": datetime.utcnow().isoformat(),
        })
