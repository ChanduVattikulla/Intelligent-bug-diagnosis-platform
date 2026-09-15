"""Validation for diagnosis input quality before agents or retrieval run."""

import re

PLACEHOLDER_VALUES = {
    "asdf",
    "asdfgh",
    "asdfghjkl",
    "qwerty",
    "qwertyuiop",
    "test",
    "testing",
    "hello",
    "blah",
    "lorem ipsum",
    "none",
    "null",
}


def validate_diagnosis_text(title: str, description: str, stack_trace: str = "", error_log: str = "") -> str | None:
    """Return a user-facing reason when input is empty or clearly placeholder text."""
    combined = " ".join(value.strip() for value in [title, description, stack_trace, error_log] if value and value.strip())
    if not combined:
        return "Please describe the bug or provide a log before submitting."

    normalized = re.sub(r"[^a-z0-9\s]", "", combined.lower()).strip()
    placeholder_words = normalized.split()
    if normalized in PLACEHOLDER_VALUES or (
        placeholder_words and all(word in PLACEHOLDER_VALUES for word in placeholder_words)
    ):
        return "Please provide real bug details instead of placeholder text."

    letters = re.findall(r"[a-z]", normalized)
    words = re.findall(r"[a-z0-9_./:-]+", combined.lower())
    if len(letters) < 4:
        return "Please provide a little more detail so the agents can analyze the problem."
    if len(words) == 1 and len(letters) < 6 and not any(marker in combined.lower() for marker in ["error", "exception", "trace", "failed", "crash"]):
        return "Please describe what failed, where it failed, and what you expected to happen."
    if len(letters) >= 8 and (len(set(letters)) < 3 or (len(letters) <= 30 and len(set(letters)) / len(letters) < 0.25)):
        return "The submission looks like placeholder text. Please provide real bug details."
    if len(letters) >= 8 and not re.search(r"[aeiou]", normalized) and "exception" not in normalized and "error" not in normalized:
        return "The submission does not look like a readable bug report. Please add a description or log."
    return None