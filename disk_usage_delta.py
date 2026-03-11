#!/usr/bin/env python3
"""
Disk Usage Delta - Track disk usage changes over time.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".disk-usage-delta"
SNAPSHOTS_FILE = DATA_DIR / "snapshots.json"


def ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SNAPSHOTS_FILE.exists():
        with open(SNAPSHOTS_FILE, "w") as f:
            json.dump({"snapshots": []}, f)


def load_snapshots():
    """Load all snapshots from the JSON file."""
    if not SNAPSHOTS_FILE.exists():
        return []
    with open(SNAPSHOTS_FILE, "r") as f:
        data = json.load(f)
    return data.get("snapshots", [])


def save_snapshots(snapshots):
    """Save snapshots to the JSON file."""
    ensure_data_dir()
    with open(SNAPSHOTS_FILE, "w") as f:
        json.dump({"snapshots": snapshots}, f, indent=2)


def get_disk_usage(path):
    """Get disk usage statistics for a given path."""
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        available = stat.f_bavail * stat.f_frsize
        used = total - free
        percent_used = (used / total * 100) if total > 0 else 0
        return {
            "path": str(path),
            "total": total,
            "used": used,
            "free": free,
            "available": available,
            "percent_used": round(percent_used, 2),
        }
    except OSError as e:
        print(f"Error getting disk usage for {path}: {e}", file=sys.stderr)
        return None


def format_size(bytes_value):
    """Format bytes into human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def take_snapshot(label=None):
    """Take a snapshot of current disk usage."""
    ensure_data_dir()
    snapshots = load_snapshots()
    
    timestamp = datetime.now().isoformat()
    if not label:
        label = f"snapshot-{len(snapshots) + 1}"
    
    root_usage = get_disk_usage("/")
    if not root_usage:
        print("Failed to get disk usage", file=sys.stderr)
        return False
    
    snapshot = {
        "id": len(snapshots) + 1,
        "label": label,
        "timestamp": timestamp,
        "usage": root_usage,
    }
    
    snapshots.append(snapshot)
    save_snapshots(snapshots)
    print(f"Snapshot #{snapshot['id']} saved: {label}")
    print(f"  Time: {timestamp}")
    print(f"  Used: {format_size(root_usage['used'])} / {format_size(root_usage['total'])} ({root_usage['percent_used']}%)")
    return True


def list_snapshots():
    """List all saved snapshots."""
    snapshots = load_snapshots()
    if not snapshots:
        print("No snapshots found. Take one with: disk-usage-delta snapshot")
        return
    
    print(f"{'ID':<6} {'Label':<20} {'Timestamp':<25} {'Used':<15}")
    print("-" * 70)
    for snap in snapshots:
        usage = snap.get("usage", {})
        used = format_size(usage.get("used", 0))
        print(f"{snap['id']:<6} {snap['label']:<20} {snap['timestamp']:<25} {used:<15}")


def show_delta(id1, id2):
    """Show the delta between two snapshots."""
    snapshots = load_snapshots()
    if not snapshots:
        print("No snapshots found", file=sys.stderr)
        return
    
    snap1 = next((s for s in snapshots if s["id"] == id1), None)
    snap2 = next((s for s in snapshots if s["id"] == id2), None)
    
    if not snap1:
        print(f"Snapshot #{id1} not found", file=sys.stderr)
        return
    if not snap2:
        print(f"Snapshot #{id2} not found", file=sys.stderr)
        return
    
    usage1 = snap1.get("usage", {})
    usage2 = snap2.get("usage", {})
    
    used_delta = usage2.get("used", 0) - usage1.get("used", 0)
    free_delta = usage2.get("free", 0) - usage1.get("free", 0)
    percent_delta = usage2.get("percent_used", 0) - usage1.get("percent_used", 0)
    
    print(f"Disk Usage Delta: {snap1['label']} -> {snap2['label']}")
    print(f"Time range: {snap1['timestamp']} to {snap2['timestamp']}")
    print()
    print(f"{'Metric':<20} {'Before':<15} {'After':<15} {'Change':<15}")
    print("-" * 65)
    
    before_used = format_size(usage1.get("used", 0))
    after_used = format_size(usage2.get("used", 0))
    change_used = f"{'+' if used_delta >= 0 else ''}{format_size(used_delta)}"
    print(f"{'Used':<20} {before_used:<15} {after_used:<15} {change_used:<15}")
    
    before_free = format_size(usage1.get("free", 0))
    after_free = format_size(usage2.get("free", 0))
    change_free = f"{'+' if free_delta >= 0 else ''}{format_size(free_delta)}"
    print(f"{'Free':<20} {before_free:<15} {after_free:<15} {change_free:<15}")
    
    before_pct = usage1.get("percent_used", 0)
    after_pct = usage2.get("percent_used", 0)
    change_pct = f"{'+' if percent_delta >= 0 else ''}{percent_delta:.2f}%"
    print(f"{'Percent Used':<20} {before_pct:<15.2f} {after_pct:<15.2f} {change_pct:<15}")
    
    if used_delta > 0:
        print(f"\nWarning: Disk usage increased by {format_size(used_delta)}")
    elif used_delta < 0:
        print(f"\nGood: Disk usage decreased by {format_size(abs(used_delta))}")
    else:
        print("\nNo change in disk usage")


def delete_snapshot(snapshot_id):
    """Delete a snapshot by ID."""
    snapshots = load_snapshots()
    original_count = len(snapshots)
    snapshots = [s for s in snapshots if s["id"] != snapshot_id]
    
    if len(snapshots) == original_count:
        print(f"Snapshot #{snapshot_id} not found", file=sys.stderr)
        return False
    
    for i, snap in enumerate(snapshots, 1):
        snap["id"] = i
    
    save_snapshots(snapshots)
    print(f"Snapshot #{snapshot_id} deleted")
    return True


def show_latest():
    """Show the latest snapshot."""
    snapshots = load_snapshots()
    if not snapshots:
        print("No snapshots found")
        return
    
    latest = snapshots[-1]
    usage = latest.get("usage", {})
    
    print(f"Latest Snapshot: {latest['label']}")
    print(f"  Time: {latest['timestamp']}")
    print(f"  Total: {format_size(usage.get('total', 0))}")
    print(f"  Used: {format_size(usage.get('used', 0))}")
    print(f"  Free: {format_size(usage.get('free', 0))}")
    print(f"  Available: {format_size(usage.get('available', 0))}")
    print(f"  Percent Used: {usage.get('percent_used', 0)}%")


def main():
    parser = argparse.ArgumentParser(
        description="Track disk usage changes over time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("snapshot", help="Take a disk usage snapshot")
    subparsers.add_parser("list", help="List all snapshots")
    subparsers.add_parser("latest", help="Show the latest snapshot")
    
    delta_parser = subparsers.add_parser("delta", help="Show delta between snapshots")
    delta_parser.add_argument("before", type=int, help="Snapshot ID to compare from")
    delta_parser.add_argument("after", type=int, help="Snapshot ID to compare to")
    
    delete_parser = subparsers.add_parser("delete", help="Delete a snapshot")
    delete_parser.add_argument("id", type=int, help="Snapshot ID to delete")
    
    args = parser.parse_args()
    
    if args.command == "snapshot":
        take_snapshot()
    elif args.command == "list":
        list_snapshots()
    elif args.command == "latest":
        show_latest()
    elif args.command == "delta":
        show_delta(args.before, args.after)
    elif args.command == "delete":
        delete_snapshot(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
