"""Quick debug script to test Logfire query."""
import sys
sys.path.insert(0, '.')

from logs.logfire_export import _query_logfire

# Test 1: Simple query to see schema
print("Test 1: Simple query...")
try:
    result = _query_logfire("SELECT * FROM records LIMIT 3")
    print(f"Got {len(result)} records")
    if result:
        print(f"First record keys: {result[0].keys()}")
        print(f"First record: {result[0]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Check what timestamps look like
print("\nTest 2: Check timestamps...")
try:
    result = _query_logfire("SELECT start_timestamp, end_timestamp FROM records LIMIT 3")
    print(f"Got {len(result)} records")
    for r in result:
        print(f"  start: {r.get('start_timestamp')}, end: {r.get('end_timestamp')}")
except Exception as e:
    print(f"Error: {e}")
