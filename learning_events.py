from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class LearningEventType(Enum):
    ANALYSIS_SUCCEEDED = "analysis_succeeded"
    FOLLOW_UP_SUCCEEDED = "follow_up_succeeded"
    FILE_ANALYZED = "file_analyzed"
    DATA_EXTRACTED = "data_extracted"
    CHART_CREATED = "chart_created"
    EXCEL_EXPORTED = "excel_exported"
    RESULT_SAVED = "result_saved"
    RESULTS_COMPARED = "results_compared"
    CUSTOM_PROMPT_SUCCEEDED = "custom_prompt_succeeded"


@dataclass(frozen=True)
class LearningEvent:
    event_type: LearningEventType
    operation_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.now)

    @property
    def deduplication_key(self) -> str:
        if self.operation_id:
            return f"{self.event_type.value}:{self.operation_id}"
        return self.id
