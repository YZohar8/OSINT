from typing import Dict

# LocalDB
LOCAL_DB: Dict[str, dict] = {}

def save_scan(scan_id: str, data: dict):
    LOCAL_DB[scan_id] = data

def update_scan(scan_id: str, updates: dict):
    if scan_id in LOCAL_DB:
        LOCAL_DB[scan_id].update(updates)

def get_scan(scan_id: str) -> dict:
    return LOCAL_DB.get(scan_id)

def get_all_scans() -> list:
    return list(LOCAL_DB.values())