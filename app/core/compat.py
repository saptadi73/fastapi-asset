from datetime import timezone
from enum import Enum

try:
    from datetime import UTC as UTC
except ImportError:  # pragma: no cover - Python < 3.11
    UTC = timezone.utc

try:
    from enum import StrEnum as StrEnum
except ImportError:  # pragma: no cover - Python < 3.11
    class StrEnum(str, Enum):
        pass
