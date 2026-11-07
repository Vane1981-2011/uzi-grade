"""Minimal QR Code encoder (byte mode, EC level L, versions 1-4).

Why hand-rolled: the tool promises *zero runtime dependencies*.  A badge that
cannot render its own re-computation code without `pip install qrcode` would be
a badge that silently degrades in a clean environment.

Scope is deliberately narrow -- versions 1-4 at EC level L hold up to 78 bytes,
which is exactly enough for ``sha256:<64 hex chars>`` (71 bytes).
"""
from __future__ import annotations

# version -> (data codewords, ec codewords per block, blocks)
_SPEC = {
    1: (19, 7, 1),
    2: (34, 10, 1),
    3: (55, 15, 1),
    4: (80, 20, 1),
}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26]}


def _gf_mul(x: int, y: int) -> int:
    """Carry-less multiply in GF(2^8), reduced by the QR primitive 0x11D."""
    z = 0
    for i in range(8):
        if y & (1 << i):
            z ^= x << i
    for i in range(15, 7, -1):
        if z & (1 << i):
            z ^= 0x11D << (i - 8)
    return z & 0xFF


def _gf_exp(n: int) -> int:
    v = 1
    for _ in range(n):
        v = _gf_mul(v, 2)
    return v


def _rs_generator(degree: int) -> list[int]:
    poly = [1]
    for i in range(degree):
        nxt = [0] * (len(poly) + 1)
        for j, c in enumerate(poly):
            nxt[j] ^= c
            nxt[j + 1] ^= _gf_mul(c, _gf_exp(i))
        poly = nxt
    return poly


def _rs_remainder(data: list[int], degree: int) -> list[int]:
    """Remainder of data(x)*x^degree divided by the QR generator polynomial.

    Plain long division (O(n*d)) -- the corpus is small and an explicit
    algorithm is easier to audit than a shift-register trick.
    """
    gen = _rs_generator(degree)
    rem = list(data) + [0] * degree
    for i in range(len(data)):
        factor = rem[i]
        if factor:
            for j in range(degree + 1):
                rem[i + j] ^= _gf_mul(gen[j], factor)
    return rem[len(data):]


def _bch_format(data: int) -> int:
    rem = data << 10
    for i in range(14, 9, -1):
        if rem & (1 << i):
            rem ^= 0x537 << (i - 10)
    return ((data << 10) | rem) ^ 0x5412


def _bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _encode_data(payload: bytes) -> tuple[int, list[int]]:
    version = 0
    data_cw = 0
    for candidate in sorted(_SPEC):
        cap = _SPEC[candidate][0] - 2  # 4-bit mode + 8-bit count = 1.5 bytes
        if len(payload) <= cap:
            version, data_cw = candidate, _SPEC[candidate][0]
            break
    if not version:
        raise ValueError(f"payload too large for QR v4-L: {len(payload)} bytes")

    bits: list[int] = []
    bits += _bits(0b0100, 4)        # byte mode
    bits += _bits(len(payload), 8)  # char count (v1-9)
    for b in payload:
        bits += _bits(b, 8)
    cap_bits = data_cw * 8
    bits += [0] * min(4, cap_bits - len(bits))
    while len(bits) % 8:
        bits.append(0)
    codewords = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = [0xEC, 0x11]
    i = 0
    while len(codewords) < data_cw:
        codewords.append(pad[i % 2])
        i += 1
    return version, codewords


def _mask_bit(mask: int, r: int, c: int) -> bool:
    return [
        (r + c) % 2 == 0,
        r % 2 == 0,
        c % 3 == 0,
        (r + c) % 3 == 0,
        (r // 2 + c // 3) % 2 == 0,
        (r * c) % 2 + (r * c) % 3 == 0,
        ((r * c) % 2 + (r * c) % 3) % 2 == 0,
        ((r + c) % 2 + (r * c) % 3) % 2 == 0,
    ][mask]


def _build(version: int, codewords: list[int], mask: int) -> list[list[int]]:
    size = 17 + 4 * version
    _, ec_cw, _ = _SPEC[version]
    stream = codewords + _rs_remainder(codewords, ec_cw)
    bits: list[int] = []
    for cw in stream:
        bits += _bits(cw, 8)

    mod: list[list[int]] = [[0] * size for _ in range(size)]
    fn: list[list[bool]] = [[False] * size for _ in range(size)]

    def place_finder(r0: int, c0: int) -> None:
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = r0 + r, c0 + c
                if 0 <= rr < size and 0 <= cc < size:
                    dark = 0 <= r <= 6 and 0 <= c <= 6 and (
                        r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4)
                    )
                    mod[rr][cc] = 1 if dark else 0
                    fn[rr][cc] = True

    place_finder(0, 0)
    place_finder(0, size - 7)
    place_finder(size - 7, 0)

    for i in range(8, size - 8):
        v = 1 if i % 2 == 0 else 0
        mod[6][i] = mod[i][6] = v
        fn[6][i] = fn[i][6] = True

    for r0 in _ALIGN[version]:
        for c0 in _ALIGN[version]:
            if (r0 < 9 and c0 < 9) or (r0 < 9 and c0 > size - 10) or (r0 > size - 10 and c0 < 9):
                continue
            for r in range(-2, 3):
                for c in range(-2, 3):
                    mod[r0 + r][c0 + c] = 1 if max(abs(r), abs(c)) in (0, 2) else 0
                    fn[r0 + r][c0 + c] = True

    # Format-information cells (two copies), indexed by bit number 0 (LSB) ..
    # 14 (MSB) as fixed by ISO/IEC 18004 section 8.9.  Copy 1 runs vertically
    # down column 8; copy 2 runs horizontally along row 8.
    copy1 = (
        [(i, 8) for i in range(6)]
        + [(7, 8), (8, 8)]
        + [(size - 15 + i, 8) for i in range(8, 15)]
    )
    copy2 = (
        [(8, size - 1 - i) for i in range(8)]
        + [(8, 7)]
        + [(8, 15 - i - 1) for i in range(9, 15)]
    )
    for r, c in copy1 + copy2:
        fn[r][c] = True
    mod[size - 8][8] = 1
    fn[size - 8][8] = True

    fmt = _bch_format((0b01 << 3) | mask)  # 01 = EC level L
    for i, (r, c) in enumerate(copy1):
        mod[r][c] = (fmt >> i) & 1
    for i, (r, c) in enumerate(copy2):
        mod[r][c] = (fmt >> i) & 1

    idx = 0
    upward = True
    col = size - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for c in (col, col - 1):
                if not fn[row][c]:
                    bit = bits[idx] if idx < len(bits) else 0
                    idx += 1
                    mod[row][c] = bit ^ (1 if _mask_bit(mask, row, c) else 0)
        upward = not upward
        col -= 2
    return mod


def _penalty(mod: list[list[int]]) -> int:
    size = len(mod)
    score = 0
    lines = list(mod) + [list(col) for col in zip(*mod)]
    for line in lines:
        run = 1
        for i in range(1, size):
            if line[i] == line[i - 1]:
                run += 1
                if run == 5:
                    score += 3
                elif run > 5:
                    score += 1
            else:
                run = 1
    # Rule 3: 1:1:3:1:1 finder-like pattern with four light modules on a side.
    pattern = "1011101"
    for line in lines:
        s = "".join(str(v) for v in line)
        for i in range(len(s) - 6):
            if s[i:i + 7] == pattern:
                before = s[max(0, i - 4):i]
                after = s[i + 7:i + 11]
                if before.count("0") == 4 or after.count("0") == 4:
                    score += 40
    for r in range(size - 1):
        for c in range(size - 1):
            if mod[r][c] == mod[r][c + 1] == mod[r + 1][c] == mod[r + 1][c + 1]:
                score += 3
    dark = sum(sum(row) for row in mod)
    total = size * size
    score += (abs(dark * 100 // total - 50) // 5) * 10
    return score


def encode(text: str) -> list[list[int]]:
    """Return a QR module matrix (1 = dark) for `text`."""
    version, codewords = _encode_data(text.encode("utf-8"))
    best: list[list[int]] | None = None
    best_score = -1
    for mask in range(8):
        mod = _build(version, codewords, mask)
        s = _penalty(mod)
        if best is None or s < best_score:
            best, best_score = mod, s
    assert best is not None
    return best


def to_svg_path(mod: list[list[int]], x0: float, y0: float, module: float) -> str:
    """Compact SVG path data for the dark modules."""
    parts: list[str] = []
    size = len(mod)
    for r in range(size):
        run_start = None
        for c in range(size + 1):
            dark = c < size and mod[r][c] == 1
            if dark and run_start is None:
                run_start = c
            elif not dark and run_start is not None:
                width = c - run_start
                parts.append(
                    f"M{x0 + run_start * module:.0f} {y0 + r * module:.0f}"
                    f"h{width * module:.0f}v{module:.0f}h{-width * module:.0f}z"
                )
                run_start = None
    return "".join(parts)
