from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CIErrorRequest(BaseModel):
    """Request model for CI error analysis"""
    command: str = Field(..., description="The command that was run")
    stdout: str = Field(..., description="Standard output from the command")
    stderr: str = Field(..., description="Standard error from the command")
    environment: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the CI environment")


class CIErrorResponse(BaseModel):
    """Response model for CI error analysis"""
    solution: str = Field(..., description="Proposed solution for the error")
    explanation: str = Field(..., description="Explanation of the error cause")
    code_change: Optional[str] = Field(None, description="Suggested code change")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Formatted content blocks")