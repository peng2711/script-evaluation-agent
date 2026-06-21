from pydantic import BaseModel, Field
from typing import Optional

class ScriptSubmission(BaseModel):
    title: str = Field(..., description="剧本或项目名称")
    content: str = Field(..., description="剧本文本、剧情简介或分集大纲内容")
    author: Optional[str] = Field(None, description="作者")
    genre: Optional[str] = Field(None, description="题材类型，如悬疑、都市、科幻等")
