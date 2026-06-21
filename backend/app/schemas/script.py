from pydantic import BaseModel, Field
from typing import Optional, List

class ScriptInput(BaseModel):
    project_id: str = Field(..., description="项目唯一ID")
    title: str = Field(..., description="剧本/项目标题")
    raw_text: str = Field(..., description="剧本正文、大纲或分集剧情原文")
    genre: Optional[str] = Field(None, description="剧本题材类型")
    target_audience: Optional[str] = Field(None, description="目标受众画像")
    user_preferences: List[str] = Field(default_factory=list, description="用户个性化偏好配置（如：偏好节奏明快、防雷点等）")
