"""
Logfire log export functions.

Exports logs from Logfire to local JSON files using the Logfire Query API.
See: https://logfire.pydantic.dev/docs/how-to-guides/query-api/
"""

import os
import json
import httpx
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LOGFIRE_READ_TOKEN = os.getenv("LOGFIRE_READ_TOKEN")

# Export directory
EXPORTS_DIR = Path(__file__).parent / "exports"

# Logfire Query API endpoint (use US region, change to logfire-eu.pydantic.dev for EU)
LOGFIRE_QUERY_URL = "https://logfire-us.pydantic.dev/v1/query"


def _ensure_exports_dir():
    """Create exports directory if it doesn't exist."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _query_logfire(sql: str, limit: int = 10000) -> List[Dict[str, Any]]:
    """
    Execute a SQL query against Logfire Query API.
    
    Args:
        sql: SQL query string
        limit: Maximum number of rows to return (default 10000, max 10000)
        
    Returns:
        List of log records as dictionaries
    """
    if not LOGFIRE_READ_TOKEN:
        raise ValueError("LOGFIRE_READ_TOKEN not found in environment variables")
    
    headers = {
        "Authorization": f"Bearer {LOGFIRE_READ_TOKEN}",
    }
    
    # Use GET request with query parameters as per docs
    params = {
        "sql": sql,
        "limit": limit,
    }
    
    response = httpx.get(LOGFIRE_QUERY_URL, headers=headers, params=params, timeout=60.0)
    
    if response.status_code != 200:
        raise Exception(f"Logfire API error {response.status_code}: {response.text}")
    
    data = response.json()
    
    # Column-oriented format: {"columns": [{"name": "col1", "values": [...]}, ...]}
    if "columns" in data and isinstance(data["columns"], list):
        columns = data["columns"]
        if not columns:
            return []
        
        # Get column names and values
        col_names = [col["name"] for col in columns]
        col_values = [col.get("values", []) for col in columns]
        
        # Transpose to row-oriented
        num_rows = len(col_values[0]) if col_values else 0
        rows = []
        for i in range(num_rows):
            row = {col_names[j]: col_values[j][i] for j in range(len(col_names))}
            rows.append(row)
        return rows
    
    # Alternative: already row-oriented list of dicts
    if isinstance(data, list):
        return data
    
    return []


def export_daily_logs(target_date: Optional[date] = None) -> dict:
    """
    Export all logs for a specific day to a JSON file.
    
    Args:
        target_date: The date to export logs for (default: today)
        
    Returns:
        Dictionary with success status, filepath, and record count
    """
    if target_date is None:
        target_date = date.today()
    
    _ensure_exports_dir()
    
    try:
        # Calculate start and end of day
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        print(f"📥 Exporting logs for {target_date}...")
        
        # Query logs for the day
        # Using end_timestamp as per Logfire schema
        query = f"""
        SELECT 
            end_timestamp,
            start_timestamp,
            trace_id,
            span_id,
            level,
            message,
            attributes,
            service_name,
            span_name
        FROM records
        WHERE end_timestamp >= '{start_time.isoformat()}'
          AND end_timestamp <= '{end_time.isoformat()}'
        ORDER BY end_timestamp DESC
        LIMIT 50000
        """
        
        logs = _query_logfire(query)
        
        # Generate filename
        filename = f"logs_{target_date.isoformat()}.json"
        filepath = EXPORTS_DIR / filename
        
        # Prepare export data
        export_data = {
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "date": target_date.isoformat(),
                "record_count": len(logs)
            },
            "logs": logs
        }
        
        # Write to JSON file (overwrite if exists - one file per day)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Exported {len(logs)} logs to {filepath}")
        
        return {
            "success": True,
            "filepath": str(filepath),
            "record_count": len(logs),
            "date": target_date.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return {"success": False, "error": str(e)}


def export_run_logs(run_start_time: Optional[datetime] = None) -> dict:
    """
    Export logs from a specific supervisor run.
    
    Call this at the end of a supervisor run to save that run's logs.
    
    Args:
        run_start_time: When the run started (default: 1 hour ago)
        
    Returns:
        Dictionary with success status, filepath, and record count
    """
    if run_start_time is None:
        run_start_time = datetime.utcnow() - timedelta(hours=1)
    
    end_time = datetime.utcnow()
    
    _ensure_exports_dir()
    
    try:
        print(f"📥 Exporting run logs from {run_start_time.isoformat()} to {end_time.isoformat()}...")
        
        # Query logs for the run period
        query = f"""
        SELECT 
            end_timestamp,
            start_timestamp,
            trace_id,
            span_id,
            level,
            message,
            attributes,
            service_name,
            span_name
        FROM records
        WHERE end_timestamp >= '{run_start_time.isoformat()}'
          AND end_timestamp <= '{end_time.isoformat()}'
        ORDER BY end_timestamp ASC
        LIMIT 50000
        """
        
        logs = _query_logfire(query)
        
        # Generate filename with run timestamp
        run_id = run_start_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"run_{run_id}.json"
        filepath = EXPORTS_DIR / filename
        
        # Prepare export data
        export_data = {
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "run_start": run_start_time.isoformat(),
                "run_end": end_time.isoformat(),
                "record_count": len(logs)
            },
            "logs": logs
        }
        
        # Write to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Exported {len(logs)} run logs to {filepath}")
        
        return {
            "success": True,
            "filepath": str(filepath),
            "record_count": len(logs),
            "run_start": run_start_time.isoformat(),
            "run_end": end_time.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Run export failed: {e}")
        return {"success": False, "error": str(e)}


def export_all_history(days_back: int = 60, delay_seconds: float = 2.0) -> dict:
    """
    Export all log history for the last N days.
    
    Args:
        days_back: Number of days to export (default: 60)
        delay_seconds: Delay between API calls to avoid rate limits (default: 2.0)
        
    Returns:
        Dictionary with success status and list of exported files
    """
    print(f"📥 Exporting logs for last {days_back} days (with {delay_seconds}s delay between requests)...")
    
    exported_files = []
    failed_dates = []
    
    for i in range(days_back):
        target_date = date.today() - timedelta(days=i)
        result = export_daily_logs(target_date)
        
        if result.get("success"):
            exported_files.append(result["filepath"])
        else:
            failed_dates.append(target_date.isoformat())
        
        # Rate limiting delay (skip on last iteration)
        if i < days_back - 1:
            time.sleep(delay_seconds)
    
    print(f"\n✅ Exported {len(exported_files)} files")
    if failed_dates:
        print(f"⚠️ Failed dates: {failed_dates}")
    
    return {
        "success": len(failed_dates) == 0,
        "exported_files": exported_files,
        "failed_dates": failed_dates,
        "total_files": len(exported_files)
    }
