"""Convert a pasted raw file (messages separated by BLANK LINES) into the
--- separated format that collect.py expects. Keeps your raw data on your
own machine; nothing leaves the laptop."""
import re
import sys
from pathlib import Path

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/raw_paste.txt")
dst = Path("data/raw/inbox.txt")

if not src.exists():
    print(f"Put your raw messages in {src} first (one message per block, blank line between messages).")
    sys.exit(1)

text = src.read_text(encoding="utf-8")
# split on one or more blank lines
blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
dst.write_text("\n---\n".join(blocks), encoding="utf-8")
print(f"Wrote {len(blocks)} messages to {dst}")