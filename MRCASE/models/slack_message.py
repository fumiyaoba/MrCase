from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class SlackMessage:
    text: str
    user: Optional[str]
    ts: str
    thread_ts: Optional[str]
    raw: Dict[str, Any]