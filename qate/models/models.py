from dataclasses import dataclass

from pydantic import BaseModel

class QAResponse(BaseModel):
    success: bool
    id: int

class QARequestBuilds(BaseModel):
    package_name: str
    success: bool
    timestamp: str
    architecture: str
    buildbot: str
    failure_reason: str
