# disk-usage-delta

Track disk usage changes over time. Because sometimes you need to know what ate all your disk space.

## Why I Built This

Ever had your disk suddenly full and no idea what happened? This tool lets you take snapshots of disk usage and compare them later. Simple as that.

## Installation

```bash
# Make it executable
chmod +x disk_usage_delta.py

# Either run it directly
./disk_usage_delta.py --help

# Or symlink it somewhere in your PATH
ln -s $(pwd)/disk_usage_delta.py ~/.local/bin/disk-usage-delta
```

No dependencies required. Just Python 3.

## Usage

### Take a snapshot

```bash
disk-usage-delta snapshot
disk-usage-delta snapshot "before-cleanup"
```

### List all snapshots

```bash
disk-usage-delta list
```

Output looks like:
```
ID     Label                Timestamp                 Used           
----------------------------------------------------------------------
1      snapshot-1           2026-03-11T10:30:00       45.20 GB       
2      before-cleanup       2026-03-11T14:00:00       52.10 GB       
```

### Compare two snapshots

```bash
disk-usage-delta delta 1 2
```

Shows you exactly how much space changed between snapshot 1 and 2.

### See the latest snapshot

```bash
disk-usage-delta latest
```

### Delete a snapshot

```bash
disk-usage-delta delete 3
```

## Where Data Is Stored

Snapshots live in `~/.disk-usage-delta/snapshots.json`. It's just JSON, so you can peek at it if you want.

## Typical Workflow

```bash
# Take a snapshot before doing something risky
disk-usage-delta snapshot "before-apt-upgrade"

# Do your thing...

# Take another snapshot after
disk-usage-delta snapshot "after-apt-upgrade"

# See what changed
disk-usage-delta delta 1 2
```

## Notes

- Only tracks the root filesystem (`/`)
- Uses `os.statvfs` so it works on Linux and macOS
- No network calls, no telemetry, nothing fancy
