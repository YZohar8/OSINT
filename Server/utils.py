import asyncio
import json
import re
import logging
from collections import defaultdict
from asyncio.exceptions import TimeoutError

logger = logging.getLogger("uvicorn")

DOMAIN_REGEX = re.compile(r"^(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$")

def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_REGEX.fullmatch(domain))

async def run_theharvester(domain: str, scan_id: str) -> dict:
    logger.info("Running theHarvester", extra={"scan_id": scan_id})
    process = await asyncio.create_subprocess_exec(
        "theHarvester",
        "-d", domain,
        "-b", "all",
        "-f", f"/tmp/harvester_{scan_id}.json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    try:
        with open(f"/tmp/harvester_{scan_id}.json.json", "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error("theHarvester parsing failed", extra={"scan_id": scan_id})
        return {"error": str(e), "stdout": stdout.decode(), "stderr": stderr.decode()}

async def run_amass(domain: str, scan_id: str) -> dict:
    logger.info("Running Amass", extra={"scan_id": scan_id})
    process = await asyncio.create_subprocess_exec(
        "amass",
        "enum",
        "-d", domain,
        "-json", f"/tmp/amass_{scan_id}.json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    try:
        with open(f"/tmp/amass_{scan_id}.json", "r") as f:
            results = json.load(f)
        return results
    except Exception as e:
        logger.error("Amass parsing failed", extra={"scan_id": scan_id})
        return {"error": str(e), "stdout": stdout.decode(), "stderr": stderr.decode()}

async def run_osint_scan(domain: str, scan_id: str) -> dict:
    try:
        harvester_task = asyncio.create_task(run_theharvester(domain, scan_id))
        amass_task = asyncio.create_task(run_amass(domain, scan_id))

        harvester_data, amass_data = await asyncio.wait_for(
            asyncio.gather(harvester_task, amass_task),
            timeout=60.0  # Timeout של דקה
        )
    except TimeoutError:
        logger.warning("Scan timed out", extra={"scan_id": scan_id})
        return {"error": "Scan timed out after 60 seconds"}

    combined = defaultdict(set)

    if isinstance(harvester_data, dict):
        for category, values in harvester_data.items():
            if isinstance(values, list):
                combined[category].update(values)

    if isinstance(amass_data, list):
        for item in amass_data:
            if 'name' in item:
                combined["subdomains"].add(item["name"])

    return {k: sorted(v) for k, v in combined.items()}
