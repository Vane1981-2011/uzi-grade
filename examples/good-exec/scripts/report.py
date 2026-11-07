"""Print a deterministic word count for a text fixture."""
import argparse
import re

p = argparse.ArgumentParser(description="render a word-count report")
p.add_argument("--in", dest="inp", default="fixtures/sample.txt")
a = p.parse_args()
text = open(a.inp, encoding="utf-8").read()
print(f"words={len(re.findall(r'[A-Za-z0-9_]+', text))}")
