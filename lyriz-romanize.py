#!/usr/bin/env python3
import re, sys, subprocess
from pathlib import Path
import pykakasi
k = pykakasi.kakasi()
bangla_script = Path.home() / ".local/bin/bangla_romanize.py"
jp = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
bn = re.compile(r"[\u0980-\u09ff]")
for line in sys.stdin:
    text = line.rstrip("\n")
    if jp.search(text):
        result = " ".join(x["hepburn"] for x in k.convert(text))
    elif bn.search(text):
        p = subprocess.run([sys.executable, str(bangla_script), text], capture_output=True, text=True)
        result = p.stdout.rstrip("\n") if p.returncode == 0 else text
    else:
        result = text
    print(result, flush=True)
