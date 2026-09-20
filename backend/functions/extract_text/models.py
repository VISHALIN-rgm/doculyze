"""Shared data shapes used across Doculyze's Lambda functions.

Kept dependency-free (stdlib only) so every function can import this
without adding it to each function's own requirements.txt — copy this
file into each function folder at build time, or bundle via a Lambda
layer in a more advanced setup.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import time
import uuid


@dataclass
class RedFlag:
    issue: str
    why_it_matters: str
    severity: str  # "low" | "medium" | "high"


@dataclass
class AnalysisResult:
    document_id: str
    status: str  # "processing" | "complete" | "failed"
    document_name: Optional[str] = None
    summary: Optional[str] = None
    key_terms: List[str] = field(default_factory=list)
    red_flags: List[RedFlag] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    raw_text_preview: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self):
        return asdict(self)


def new_document_id() -> str:
    return uuid.uuid4().hex
