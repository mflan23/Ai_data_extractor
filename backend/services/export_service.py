"""Export service – converts extracted records to various output formats."""
from __future__ import annotations

import csv
import io
import json
from typing import Any


def to_json(records: list[dict[str, Any]], indent: int = 2) -> bytes:
    """Serialise records as pretty-printed JSON."""
    return json.dumps(records, ensure_ascii=False, indent=indent).encode("utf-8")


def to_jsonl(records: list[dict[str, Any]]) -> bytes:
    """Serialise records as newline-delimited JSON (one object per line)."""
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def to_csv(records: list[dict[str, Any]]) -> bytes:
    """Serialise records as CSV bytes (UTF-8 with BOM for Excel compat.)."""
    if not records:
        return b""

    buf = io.StringIO()
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")


def to_tsv(records: list[dict[str, Any]]) -> bytes:
    """Serialise records as tab-separated values."""
    if not records:
        return b""

    buf = io.StringIO()
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(
        buf, fieldnames=fieldnames, extrasaction="ignore", delimiter="\t"
    )
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue().encode("utf-8")


def to_xlsx(records: list[dict[str, Any]]) -> bytes:
    """Serialise records as an Excel workbook."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to export XLSX files") from exc

    df = pd.DataFrame(records)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Extracted Data")
    return buf.getvalue()


EXPORT_FORMATS: dict[str, tuple[str, str]] = {
    "json": ("application/json", "data.json"),
    "jsonl": ("application/x-ndjson", "data.jsonl"),
    "csv": ("text/csv", "data.csv"),
    "tsv": ("text/tab-separated-values", "data.tsv"),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "data.xlsx",
    ),
}


def export(records: list[dict[str, Any]], fmt: str) -> tuple[bytes, str, str]:
    """Return (bytes, media_type, filename) for the requested format.

    Raises ValueError for unsupported formats.
    """
    fmt = fmt.lower()
    if fmt not in EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported export format '{fmt}'. "
            f"Supported: {', '.join(EXPORT_FORMATS)}"
        )

    media_type, filename = EXPORT_FORMATS[fmt]

    if fmt == "json":
        data = to_json(records)
    elif fmt == "jsonl":
        data = to_jsonl(records)
    elif fmt == "csv":
        data = to_csv(records)
    elif fmt == "tsv":
        data = to_tsv(records)
    elif fmt == "xlsx":
        data = to_xlsx(records)
    else:
        raise ValueError(f"Unhandled format: {fmt}")

    return data, media_type, filename
