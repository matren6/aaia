import sys
from pathlib import Path

# Ensure the packages directory is on sys.path so tests can import modules
ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
if str(PACKAGES) not in sys.path:
    sys.path.insert(0, str(PACKAGES))
