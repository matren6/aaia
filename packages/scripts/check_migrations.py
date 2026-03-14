#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.migrations import get_migrations

migs = get_migrations()
print(f"Total migrations registered: {len(migs)}")
for m in migs:
    print(f"  - {m}")

