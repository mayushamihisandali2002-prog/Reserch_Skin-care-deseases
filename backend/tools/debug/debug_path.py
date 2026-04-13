import os
from pathlib import Path
print(f"CWD: {os.getcwd()}")
print(f"File: {__file__}")
print(f"Parent: {Path(__file__).parent}")
backend_dir = Path(__file__).resolve().parents[2]
local_ffmpeg_dir = backend_dir / "ffmpeg"
print(f"FFMPEG Dir exists: {local_ffmpeg_dir.exists()}")
for found in local_ffmpeg_dir.rglob("ffmpeg.exe"):
    print(f"Found: {found}")
