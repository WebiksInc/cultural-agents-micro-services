"""
Manual log export script.

Run this script to export Logfire logs to local JSON files.

Usage:
    python logs/run_export.py              # Export today's logs
    python logs/run_export.py --days 7     # Export last 7 days
    python logs/run_export.py --all        # Export all history (60 days)
"""

import argparse
import time
from datetime import date, timedelta

from logfire_export import export_daily_logs, export_run_logs, export_all_history


def main():
    parser = argparse.ArgumentParser(description="Export Logfire logs to JSON files")
    parser.add_argument("--days", type=int, default=1, help="Number of days to export (default: 1)")
    parser.add_argument("--all", action="store_true", help="Export all history (60 days)")
    parser.add_argument("--date", type=str, help="Specific date to export (YYYY-MM-DD)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between API calls in seconds (default: 2.0)")
    
    args = parser.parse_args()
    
    if args.all:
        print("🚀 Exporting all log history...")
        result = export_all_history(delay_seconds=args.delay)
        print(f"\n📊 Summary: {result}")
        
    elif args.date:
        # Parse specific date
        try:
            target_date = date.fromisoformat(args.date)
            print(f"🚀 Exporting logs for {target_date}...")
            result = export_daily_logs(target_date)
            print(f"\n📊 Result: {result}")
        except ValueError:
            print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD")
            return
            
    elif args.days > 1:
        print(f"🚀 Exporting logs for last {args.days} days...")
        for i in range(args.days):
            target_date = date.today() - timedelta(days=i)
            result = export_daily_logs(target_date)
            if not result.get("success"):
                print(f"  ⚠️ Failed: {result.get('error')}")
            # Rate limiting delay
            if i < args.days - 1:
                time.sleep(args.delay)
        print("\n✅ Done!")
        
    else:
        # Default: export today
        print("🚀 Exporting today's logs...")
        result = export_daily_logs()
        print(f"\n📊 Result: {result}")


if __name__ == "__main__":
    main()
