# backend/app/services/data_cleaning.py
"""
Cleans and standardizes raw historical bug data (from Mozilla/Apache/Eclipse
Kaggle exports, which each use slightly different column names) into one
common schema used everywhere downstream:

    bug_id, source, product, component, summary, description,
    stack_trace, comments, resolution, status, created_date

Kaggle bug-report dumps vary by dataset. Common column-name variants are
mapped in COLUMN_ALIASES below — add to it if a dataset you download uses
different names than what's already covered.
"""

import re
import pandas as pd

STANDARD_COLUMNS = [
    "bug_id", "source", "product", "component", "summary", "description",
    "stack_trace", "comments", "resolution", "status", "priority", "severity", "created_date",
]

# Left side: our standard column name. Right side: variant names seen across
# public Mozilla/Apache/Eclipse bug-report CSV exports on Kaggle and other
# public bug-tracker research datasets (e.g. Bugzilla-style exports).
COLUMN_ALIASES = {
    "bug_id": ["bug_id", "id", "issue_id", "bugid"],
    "product": ["product", "project", "product_name"],
    "component": ["component", "module", "component_name"],
    "summary": ["summary", "title", "short_desc", "short_description"],
    "description": ["description", "desc", "long_desc", "body", "long_description"],
    "stack_trace": ["stack_trace", "stacktrace", "trace"],
    "comments": ["comments", "comment_text", "discussion"],
    "resolution": ["resolution", "fix", "resolution_text", "resolution_category", "resolution_code"],
    "status": ["status", "bug_status", "state", "status_category", "status_code"],
    "priority": ["priority"],
    "severity": ["severity", "severity_category", "severity_code"],
    "created_date": ["created_date", "creation_time", "created_time", "opened", "created_at", "creation_date"],
}

def _find_column(df: pd.DataFrame, aliases: list):
    lower_map = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias]
    return None


def _clean_text(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    # Strip control characters but keep normal whitespace/newlines.
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Collapse excessive blank lines (common in scraped bug dumps).
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def standardize_dataframe(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Maps a raw dataset's columns onto STANDARD_COLUMNS and cleans text fields."""
    out = {}
    for standard_col, aliases in COLUMN_ALIASES.items():
        found = _find_column(df, aliases)
        out[standard_col] = df[found] if found is not None else ""

    result = pd.DataFrame(out)
    result["source"] = source

    text_fields = ["summary", "description", "stack_trace", "comments", "resolution"]
    for field in text_fields:
        result[field] = result[field].apply(_clean_text)

    if _find_column(df, COLUMN_ALIASES["bug_id"]) is None:
        result["bug_id"] = [f"{source}-{row_index}" for row_index in df.index]
    else:
        result["bug_id"] = result["bug_id"].astype(str)
        result["bug_id"] = source + "-" + result["bug_id"]
    result["priority"] = result["priority"].fillna("").astype(str)
    result["severity"] = result["severity"].fillna("").astype(str)
    result["status"] = result["status"].fillna("").astype(str)

    # Drop rows with no usable text at all — nothing to chunk/embed.
    has_content = result[text_fields].apply(lambda col: col.str.len() > 0).any(axis=1)
    result = result[has_content].reset_index(drop=True)

    return result[STANDARD_COLUMNS]
