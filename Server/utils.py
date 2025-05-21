import asyncio
import json
import re
import logging
import traceback
import os
import time
from collections import defaultdict
from asyncio.exceptions import TimeoutError

logger = logging.getLogger("uvicorn")

# Domain validation regex
DOMAIN_REGEX = re.compile(r"^(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$")

def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_REGEX.fullmatch(domain))


# theHarvester OSINT tool runner
async def run_theharvester(domain: str, scan_id: str) -> dict:
    logger.info("Running theHarvester", extra={"scan_id": scan_id})
    output_file = f"/tmp/harvester_{scan_id}.json"

    try:
        process = await asyncio.create_subprocess_exec(
            "theHarvester",
            "-d", domain,
            "-b", "all",
            "-f", output_file.replace(".json", ""),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        logger.info("theHarvester finished", extra={"scan_id": scan_id})
        logger.debug(f"stdout: {stdout.decode()}", extra={"scan_id": scan_id})
        logger.debug(f"stderr: {stderr.decode()}", extra={"scan_id": scan_id})

        result_path = output_file + ".json"
        if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
            with open(result_path, "r") as f:
                return json.load(f)
        else:
            logger.warning("theHarvester output missing or empty", extra={"scan_id": scan_id})
            return {"error": "theHarvester output missing or empty"}

    except Exception as e:
        logger.error("theHarvester failed", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        return {"error": str(e), "stdout": stdout.decode() if 'stdout' in locals() else "", "stderr": stderr.decode() if 'stderr' in locals() else ""}


# Amass OSINT tool runner
async def run_amass(domain: str, scan_id: str) -> dict:
    logger.info("Running Amass", extra={"scan_id": scan_id})
    output_file = f"/tmp/amass_{scan_id}.json"

    try:
        process = await asyncio.create_subprocess_exec(
            "amass", "enum",
            "-d", domain,
            "-json", output_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        logger.info("Amass finished", extra={"scan_id": scan_id})
        logger.debug(f"stdout: {stdout.decode()}", extra={"scan_id": scan_id})
        logger.debug(f"stderr: {stderr.decode()}", extra={"scan_id": scan_id})

        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, "r") as f:
                return json.load(f)
        else:
            logger.warning("Amass output missing or empty", extra={"scan_id": scan_id})
            return {"error": "Amass output missing or empty"}

    except Exception as e:
        logger.error("Amass failed", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        return {"error": str(e), "stdout": stdout.decode() if 'stdout' in locals() else "", "stderr": stderr.decode() if 'stderr' in locals() else ""}


# Main OSINT scan logic that runs both tools and merges results
async def run_osint_scan(domain: str, scan_id: str) -> dict:
    harvester_data = {}
    amass_data = {}

    try:
        logger.info("Starting OSINT scan", extra={"scan_id": scan_id})
        start_time = time.time()

        harvester_task = asyncio.create_task(
            asyncio.wait_for(run_theharvester(domain, scan_id), timeout=150)
        )
        amass_task = asyncio.create_task(
            asyncio.wait_for(run_amass(domain, scan_id), timeout=150)
        )

        harvester_data, amass_data = await asyncio.wait_for(
            asyncio.gather(harvester_task, amass_task),
            timeout=300  # 5 minutes
        )

        elapsed = time.time() - start_time
        logger.info(f"Scan completed in {elapsed:.2f} seconds", extra={"scan_id": scan_id})

    except TimeoutError:
        logger.warning("Scan timed out", extra={"scan_id": scan_id})
        return {"error": "Scan timed out after 5 minutes"}

    except Exception as e:
        logger.error("Unexpected error during scan", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        return {"error": f"Unexpected error: {str(e)}"}

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
