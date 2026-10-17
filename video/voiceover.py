"""Generate the voiceover lines with Piper (offline neural TTS).

pip install piper-tts, then download en_US-ryan-high.onnx and .onnx.json from
https://huggingface.co/rhasspy/piper-voices into voice/.
"""
import subprocess
from pathlib import Path

VOICE = "voice/en_US-ryan-high.onnx"
lines = Path("vo/lines.txt").read_text().strip().splitlines()
for i, line in enumerate(lines, 1):
    subprocess.run(["python3", "-m", "piper", "-m", VOICE, "-f", f"vo/line_{i}.wav"], input=line, text=True, check=True)
