"""Shared helpers: hashing, normalisation, bounded subprocess execution."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

TOOL_VERSION = "1.0.0"
SCHEMA = "uzi-grade/1"

# Volatile fragments stripped before hashing so a rerun on another day,
# in another home directory, produces the same sha256.
_VOLATILE = [
    (re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+Z?"), "<TS>"),
    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"), "<TS>"),
    (re.compile(r"/Users/[^/\s]+"), "<HOME>"),
    (re.compile(r"/tmp/[^\s:]+"), "<TMP>"),
    (re.compile(r"0x[0-9a-f]{6,}"), "<ADDR>"),
    (re.compile(r"\b\d+\.\d+s\b"), "<DUR>"),
]


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for pat, rep in _VOLATILE:
        text = pat.sub(rep, text)
    return text


def sha256_text(text: str) -> str:
    return hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(path: Path) -> str:
    """Stable hash of a directory: relative path + size + content hash."""
    entries = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"})
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            fp = Path(root) / name
            rel = fp.relative_to(path).as_posix()
            try:
                entries.append(f"{rel}\t{fp.stat().st_size}\t{sha256_file(fp)}")
            except OSError:
                entries.append(f"{rel}\tMISSING")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def run_cmd(argv: list[str], cwd: Path | None = None, timeout: int = 10) -> tuple[int, str, str]:
    """Run a bounded subprocess. Returns (rc, stdout, stderr). Timeout -> rc 124."""
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except OSError as exc:
        return 126, "", str(exc)


def python_exe() -> str:
    """Always use the interpreter running the tool, never a bare `python3`."""
    return sys.executable


def evidence(cmd: str, rc: int | None, out: str, err: str = "") -> dict:
    """Standard evidence record carried by every check."""
    payload = f"cmd={cmd}\nrc={rc}\nout={out}\nerr={err}"
    return {
        "command": cmd,
        "exit_code": rc,
        "output_sha256": sha256_text(payload),
        "stdout_tail": out.strip()[-400:],
        "stderr_tail": err.strip()[-400:],
    }
