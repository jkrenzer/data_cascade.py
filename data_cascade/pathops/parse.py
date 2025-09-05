"""Path parsing utilities for dotted and bracketed paths."""

from __future__ import annotations

from typing import List, Tuple

KeyPath = Tuple[str, ...]


def parse_path(expr: str) -> KeyPath:
    # Supports a.b[1].c and a."x.y"[2] and a["x.y"][2]
    i = 0
    n = len(expr)
    segs: List[str] = []
    buf: List[str] = []

    def flush_buf():
        if buf or not segs:
            segs.append("".join(buf))
            buf.clear()

    while i < n:
        ch = expr[i]
        if ch == ".":
            flush_buf()
            i += 1
            continue
        if ch in ("'", '"'):
            # quoted segment outside brackets
            quote = ch
            i += 1
            qbuf: List[str] = []
            while i < n and expr[i] != quote:
                if expr[i] == "\\" and i + 1 < n:
                    i += 1
                    qbuf.append(expr[i])
                else:
                    qbuf.append(expr[i])
                i += 1
            if i >= n or expr[i] != quote:
                raise ValueError("Unclosed quoted segment")
            i += 1
            # After a quoted segment, if next is [number] it will be handled in loop
            if buf:
                # buffer should be empty here normally
                pass
            segs.append("".join(qbuf))
            continue
        if ch == "[":
            # flush current dotted segment before bracket
            if buf:
                flush_buf()
            i += 1
            if i >= n:
                raise ValueError("Unclosed [")
            if expr[i] in ("'", '"'):
                quote = expr[i]
                i += 1
                qbuf: List[str] = []
                while i < n and expr[i] != quote:
                    if expr[i] == "\\" and i + 1 < n:
                        i += 1
                        qbuf.append(expr[i])
                    else:
                        qbuf.append(expr[i])
                    i += 1
                if i >= n or expr[i] != quote:
                    raise ValueError("Unclosed quote in []")
                i += 1
                if i >= n or expr[i] != "]":
                    raise ValueError("Expected ] after quoted key")
                i += 1
                segs.append("".join(qbuf))
            else:
                # index or bare key until ]
                j = expr.find("]", i)
                if j == -1:
                    raise ValueError("Unclosed ]")
                token = expr[i:j].strip()
                i = j + 1
                segs.append(token)
            continue
        # normal char in dotted segment
        buf.append(ch)
        i += 1
    flush_buf()
    segs = [s for s in segs if s != ""]
    return tuple(segs)


def join_path(*parts: KeyPath) -> KeyPath:
    out: List[str] = []
    for p in parts:
        out.extend(list(p))
    return tuple(out)
