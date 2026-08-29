from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

class QAResponse(BaseModel):
    success: bool
    id: int

class QARequestBuilds(BaseModel):
    package_name: str
    success: bool
    timestamp: datetime
    architecture: str
    buildbot: str
    failure_reason: str
