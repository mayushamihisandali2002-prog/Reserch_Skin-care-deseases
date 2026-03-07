import os
from pathlib import Path
print(f"CWD: {os.getcwd()}")
print(f"File: {__file__}")
print(f"Parent: {Path(__file__).parent}")
local_ffmpeg_dir = Path(__file__).parent / "ffmpeg"
print(f"FFMPEG Dir exists: {local_ffmpeg_dir.exists()}")
for found in local_ffmpeg_dir.rglob("ffmpeg.exe"):
    print(f"Found: {found}")
