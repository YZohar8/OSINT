import asyncio
import json
import re
import logging
import traceback
import os
import time
from collections import defaultdict
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("uvicorn")

DOMAIN_REGEX = re.compile(r"^(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$")
EXECUTOR = ThreadPoolExecutor(max_workers=5)

def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_REGEX.fullmatch(domain))



# 🧠 OSINT Source Groups for Domain Profiling
# These sources are used for gathering subdomains, emails, IPs, certificates, and more.
# Some sources require an API key (marked with 🔒).

HARVESTER_SOURCE_GROUPS = [
    # 🌐 Search Engines
    "google",        # General web search
    "bing",          # Microsoft search engine
    "yahoo",         # Search engine results
    "baidu",         # Chinese search engine
    "duckduckgo",    # Privacy-focused search

    # 👥 Social & Professional Networks
    "twitter",       # Public mentions, leaks
    "facebook",      # Public profile/content discovery (may require auth)

    # 📜 Certificate Transparency & Subdomain Enumeration
    "crtsh",             # Certificate transparency logs
    "certspotter",       # Alternative CT log aggregator
    "google-cert-transparency",  # Google's CT service
    "facebook-cert",     # Facebook's certificate disclosures
    "dnsdumpster",       # DNS recon and passive subdomain enumeration
    "rapiddns",          # Free subdomain lookup service
    "anubis",            # Passive subdomain discovery
    "sublist3r",         # Tool for discovering subdomains via multiple services
    "amass",             # Powerful asset discovery (🔒 or self-hosted)



    # 🔍 URL, DNS & WHOIS Information

    "dnsrepo",      # Public DNS records (less known)
    "whois",        # WHOIS info about domain registration
    "github",       # Sensitive data leak detection via repos (tokens, keys etc)
]

async def run_theharvester_chunked(domain: str, scan_id: str) -> dict:
    logger.info("Running theHarvester in chunks", extra={"scan_id": scan_id})
    tasks = []
    for i, sources in enumerate(HARVESTER_SOURCE_GROUPS):
        chunk_id = f"{scan_id}_harv_chunk{i}"
        tasks.append(run_theharvester_single(domain, chunk_id, sources))
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined = defaultdict(list)
    for i, result in enumerate(results):
        if isinstance(result, dict) and "error" not in result:
            for k, v in result.items():
                if isinstance(v, list):
                    combined[k].extend(v)
    return dict(combined)

async def run_theharvester_single(domain: str, chunk_id: str, sources: str) -> dict:
    logger.info(f"Running theHarvester chunk with sources: {sources}", extra={"scan_id": chunk_id})
    output_file = f"/tmp/harvester_{chunk_id}"
    try:
        process = await asyncio.create_subprocess_exec(
            "theHarvester", "-d", domain, "-b", sources, "-f", output_file,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=240)
        logger.info(f"Finished theHarvester chunk: {sources}", extra={"scan_id": chunk_id})

        result_path = output_file + ".json"
        if os.path.exists(result_path) and os.path.getsize(result_path) > 0:
            with open(result_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Missing output: {sources}", extra={"scan_id": chunk_id})
            return {}
    except TimeoutError:
        logger.warning(f"Timeout: theHarvester chunk {sources}", extra={"scan_id": chunk_id})
        return {}
    except Exception:
        logger.error(f"Error in theHarvester chunk {sources}", extra={"scan_id": chunk_id})
        logger.error(traceback.format_exc(), extra={"scan_id": chunk_id})
        return {}

AMASS_TECHNIQUES = [
    # Passive enumeration (uses passive data sources)
    {"name": "passive", "args": ["enum", "-passive", "-d", "<domain>"]},

    # Brute force with depth 1 (only direct subdomains)
    {"name": "brute_force_1_depth", "args": ["enum", "-brute", "-d", "<domain>", "-depth", "1"]},

    # Brute force with depth 2 (subdomains of subdomains)
    {"name": "brute_force_2_depth", "args": ["enum", "-brute", "-d", "<domain>", "-depth", "2"]},

    # Brute force with wordlist
    {"name": "brute_force_with_wordlist", "args": ["enum", "-brute", "-d", "<domain>", "-w", "/usr/share/wordlists/dirb/common.txt"]},

    # Brute force with wordlist and depth 2
    {"name": "brute_force_depth_2_with_wordlist", "args": ["enum", "-brute", "-d", "<domain>", "-w", "/usr/share/wordlists/dirb/common.txt", "-depth", "2"]},

    # Active enumeration with depth 1 (actively queries sources)
    {"name": "active_depth_1", "args": ["enum", "-active", "-d", "<domain>", "-depth", "1"]},

    # Active enumeration with depth 2
    {"name": "active_depth_2", "args": ["enum", "-active", "-d", "<domain>", "-depth", "2"]},

    # Active enumeration with wordlist
    {"name": "active_with_wordlist", "args": ["enum", "-active", "-d", "<domain>", "-w", "/usr/share/wordlists/dirb/common.txt"]},

    # Active enumeration with wordlist and depth 2
    {"name": "active_depth_2_with_wordlist", "args": ["enum", "-active", "-d", "<domain>", "-w", "/usr/share/wordlists/dirb/common.txt", "-depth", "2"]},
]


async def run_amass_chunked(domain: str, scan_id: str) -> list:
    logger.info("Running Amass in chunks", extra={"scan_id": scan_id})
    tasks = []
    for technique in AMASS_TECHNIQUES:
        chunk_id = f"{scan_id}_amass_{technique['name']}"
        args = [arg if arg != "<domain>" else domain for arg in technique["args"]]
        tasks.append(run_amass_single(domain, chunk_id, args))
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined = []
    for i, result in enumerate(results):
        if isinstance(result, list):
            combined.extend(result)
        elif isinstance(result, dict) and "results" in result:
            combined.extend(result["results"])
    return combined

async def run_amass_single(domain: str, chunk_id: str, args: list) -> list:
    logger.info(f"Running Amass chunk: {args}", extra={"scan_id": chunk_id})
    output_file = f"/tmp/amass_{chunk_id}.json"
    try:
        full_args = args + ["-d", domain, "-json", output_file, "-timeout", "180"]
        process = await asyncio.create_subprocess_exec(
            "amass", *full_args,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        logger.info(f"Finished Amass chunk: {args[0]}", extra={"scan_id": chunk_id})

        results = []
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                for line in f:
                    try:
                        results.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        return results
    except TimeoutError:
        logger.warning(f"Timeout in Amass chunk {args[0]}", extra={"scan_id": chunk_id})
        return []
    except Exception:
        logger.error(f"Error in Amass chunk {args[0]}", extra={"scan_id": chunk_id})
        logger.error(traceback.format_exc(), extra={"scan_id": chunk_id})
        return []

async def run_osint_scan(domain: str, scan_id: str) -> dict:
    combined = defaultdict(set)
    try:
        logger.info("Starting OSINT scan", extra={"scan_id": scan_id})
        start_time = time.time()

        harvester_task = asyncio.create_task(run_theharvester_chunked(domain, scan_id))
        amass_task = asyncio.create_task(run_amass_chunked(domain, scan_id))

        harvester_data, amass_data = await asyncio.wait_for(
            asyncio.gather(harvester_task, amass_task),
            timeout=900  # 15 minutes
        )

        if isinstance(harvester_data, dict):
            for category, values in harvester_data.items():
                if isinstance(values, list):
                    combined[category].update(values)

        if isinstance(amass_data, list):
            for item in amass_data:
                if isinstance(item, dict) and 'name' in item:
                    combined["subdomains"].add(item["name"])

        result = {k: sorted(v) for k, v in combined.items()}

        # 🧮 Build summary string
        summary = ', '.join(f"{k}: {len(v)}" for k, v in result.items())

        elapsed = time.time() - start_time
        logger.info(f"Scan completed in {elapsed:.2f} seconds and aummary is {summary}", extra={"scan_id": scan_id})

        # ⬅️ Return both result and summary

        print("result and summary")
        print("result")
        print(result)
        print("summary")
        print(summary)
        return {
            "result": result,
            "summary": summary
        }

    except TimeoutError:
        logger.warning("Global scan timeout", extra={"scan_id": scan_id})
        return {
            "result": {"error": "Scan timeout after 15 minutes"},
            "summary": "Scan failed"
        }
         
    except Exception:
        logger.error("Unexpected error", extra={"scan_id": scan_id})
        logger.error(traceback.format_exc(), extra={"scan_id": scan_id})
        return {
            "result": {"error": "Unexpected error during scan"},
            "summary": "Scan failed"
        }
         
    

