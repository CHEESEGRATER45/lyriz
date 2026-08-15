#!/usr/bin/env python3
import sys, unicodedata
from indic_transliteration import sanscript

text = sys.argv[1]
out = sanscript.transliterate(text, sanscript.BENGALI, sanscript.ITRANS)
out = unicodedata.normalize("NFKD", out).encode("ascii", "ignore").decode("ascii")
print(out)