from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field


class ListItem(BaseModel):
    """Model for an item in a list block"""
    content: str


class ParagraphBlock(BaseModel):
    """Model for a paragraph block"""
    type: Literal["paragraph"]
    content: str


class HeadingBlock(BaseModel):
    """Model for a heading block"""
    type: Literal["heading"]
    level: int = Field(ge=1, le=6)  # h1-h6
    content: str


class ListBlock(BaseModel):
    """Model for a list block"""
    type: Literal["list"]
    ordered: bool
    items: List[ListItem]


class CodeBlock(BaseModel):
    """Model for a code block"""
    type: Literal["code"]
    language: str
    content: str
    filename: Optional[str] = None
    highlight: Optional[List[int]] = None
    executable: Optional[bool] = False


class CommandBlock(BaseModel):
    """Model for a command block"""
    type: Literal["command"]
    commandType: str
    target: str
    parameters: Dict[str, Any]


class CalloutBlock(BaseModel):
    """Model for a callout block"""
    type: Literal["callout"]
    style: str
    title: Optional[str] = None
    content: str


# Union of all block types
Block = Union[
    ParagraphBlock,
    HeadingBlock,
    ListBlock,
    CodeBlock,
    CommandBlock,
    CalloutBlock
]


class ContentBlocks(BaseModel):
    """Model for the content blocks"""
    blocks: List[Block]


class ResponseMetadata(BaseModel):
    """Model for response metadata"""
    model: str
    timestamp: str


class ResponseContent(BaseModel):
    """Model for response content"""
    blocks: List[Block]


class Response(BaseModel):
    """Model for the response"""
    type: str
    metadata: ResponseMetadata
    content: ResponseContent


class JetbrainsResponse(BaseModel):
    """Model for the complete Jetbrains LLM response"""
    schema: Literal["jetbrains-llm-response"]
    version: str
    response: Response
