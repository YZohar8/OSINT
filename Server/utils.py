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

# theHarvester configuration - split sources into groups
HARVESTER_SOURCE_GROUPS = [
    "bing,google,yahoo",
    "baidu,duckduckgo",
    "linkedin,twitter",
    "dnsdumpster,threatcrowd,virustotal",
    "securitytrails,shodan"
]

# theHarvester with chunked sources
async def run_theharvester_chunked(domain: str, scan_id: str) -> dict:
    logger.info("Running theHarvester in chunks", extra={"scan_id": scan_id})
    
    # Create tasks for each group of sources
    tasks = []
    results = {}
    
    for i, sources in enumerate(HARVESTER_SOURCE_GROUPS):
        chunk_id = f"{scan_id}_chunk{i}"
        tasks.append(run_theharvester_single(domain, chunk_id, sources))
    
    # Run all tasks concurrently
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results from all chunks
    combined_results = defaultdict(list)
    for result in chunk_results:
        if isinstance(result, dict) and "error" not in result:
            for key, values in result.items():
                if isinstance(values, list):
                    combined_results[key].extend(values)
    
    return dict(combined_results)


# Run theHarvester with a specific set of sources
async def run_theharvester_single(domain: str, chunk_id: str, sources: str) -> dict:
    logger.info(f"Running theHarvester chunk with sources: {sources}", extra={"scan_id": chunk_id})
    output_file = f"/tmp/harvester_{chunk_id}"

    try:
        process = await asyncio.create_subprocess_exec(
            "theHarvester",
            "-d", domain,
            "-b", sources,
            "-f", output_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

        logger.info(f"theHarvester chunk finished: {sources}", extra={"scan_id": chunk_id})
        
        result_path = output_file + ".json"
        if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
            with open(result_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"theHarvester output missing for sources: {sources}", extra={"scan_id": chunk_id})
            return {}

    except TimeoutError:
        logger.warning(f"theHarvester chunk timed out: {sources}", extra={"scan_id": chunk_id})
        return {}
    except Exception as e:
        logger.error(f"theHarvester chunk failed: {sources}", extra={"scan_id": chunk_id})
        logger.error(traceback.format_exc(), extra={"scan_id": chunk_id})
        return {}


# Amass configuration - split techniques
AMASS_TECHNIQUES = [
    {"name": "passive", "args": ["enum", "-passive"]},
    {"name": "active_dns", "args": ["enum", "-brute", "-w", "/usr/share/wordlists/dirb/common.txt", "-d", "2"]},
    {"name": "active_web", "args": ["enum", "-active", "-d", "1"]},
]

# Amass with chunked techniques
async def run_amass_chunked(domain: str, scan_id: str) -> dict:
    logger.info("Running Amass in chunks", extra={"scan_id": scan_id})
    
    # Create tasks for each technique
    tasks = []
    
    for technique in AMASS_TECHNIQUES:
        chunk_id = f"{scan_id}_{technique['name']}"
        tasks.append(run_amass_single(domain, chunk_id, technique["args"]))
    
    # Run all tasks concurrently with overall timeout
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results from all chunks
    combined_results = []
    for result in chunk_results:
        if isinstance(result, list):
            combined_results.extend(result)
        elif isinstance(result, dict) and "results" in result and isinstance(result["results"], list):
            combined_results.extend(result["results"])
    
    return combined_results


# Run Amass with specific technique arguments
async def run_amass_single(domain: str, chunk_id: str, args: list) -> list:
    logger.info(f"Running Amass chunk: {args}", extra={"scan_id": chunk_id})
    output_file = f"/tmp/amass_{chunk_id}.json"

    try:
        full_args = list(args)  # Copy the arguments
        full_args.extend(["-d", domain, "-json", output_file, "-timeout", "90"])
        
        process = await asyncio.create_subprocess_exec(
            "amass", *full_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)

        logger.info(f"Amass chunk finished: {args[0]}", extra={"scan_id": chunk_id})
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # Amass JSON format is one JSON object per line
            results = []
            with open(output_file, "r") as f:
                for line in f:
                    try:
                        results.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            return results
        else:
            logger.warning(f"Amass output missing for technique: {args[0]}", extra={"scan_id": chunk_id})
            return []

    except TimeoutError:
        logger.warning(f"Amass chunk timed out: {args[0]}", extra={"scan_id": chunk_id})
        return []
    except Exception as e:
        logger.error(f"Amass chunk failed: {args[0]}", extra={"scan_id": chunk_id})
        logger.error(traceback.format_exc(), extra={"scan_id": chunk_id})
        return []


# Main OSINT scan logic that runs both tools and merges results
async def run_osint_scan(domain: str, scan_id: str) -> dict:
    combined = defaultdict(set)
    
    try:
        logger.info("Starting OSINT scan with chunking strategy", extra={"scan_id": scan_id})
        start_time = time.time()

        # Run both tools in parallel with chunking within each
        harvester_task = asyncio.create_task(run_theharvester_chunked(domain, scan_id))
        amass_task = asyncio.create_task(run_amass_chunked(domain, scan_id))
        
        # Wait for both tasks with overall timeout
        harvester_data, amass_data = await asyncio.wait_for(
            asyncio.gather(harvester_task, amass_task),
            timeout=600  # 10 minutes
        )

        # Process theHarvester results
        if isinstance(harvester_data, dict):
            for category, values in harvester_data.items():
                if isinstance(values, list):
                    combined[category].update(values)

        # Process Amass results
        if isinstance(amass_data, list):
            for item in amass_data:
                if isinstance(item, dict) and 'name' in item:
                    combined["subdomains"].add(item["name"])

        elapsed = time.time() - start_time
        logger.info(f"Scan completed in {elapsed:.2f} seconds", extra={"scan_id": scan_id})

    except TimeoutError:
        logger.warning("Overall scan timed out", extra={"scan_id": scan_id})
        return {"error": "Scan timed out after 10 minutes"}

    except Exception as e:
        logger.error("Unexpected error during scan", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        return {"error": f"Unexpected error: {str(e)}"}

    # Convert sets to sorted lists for JSON serialization
    return {k: sorted(v) for k, v in combined.items()}