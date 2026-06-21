import os
import json
from typing import List, Dict, Any, Optional
from .schemas import FeedbackInput

class FeedbackStore:
    """
    负责将用户反馈加载并持久化至本地 JSON 文件中。
    """
    def __init__(self, file_path: Optional[str] = None):
        if file_path:
            self.file_path = file_path
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.file_path = os.path.normpath(os.path.join(current_dir, "..", "..", "storage", "feedback.json"))
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_all(self, data: List[Dict[str, Any]]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_feedback(self, feedback: FeedbackInput) -> None:
        feedbacks = self._read_all()
        feedbacks.append(feedback.model_dump())
        self._write_all(feedbacks)

    def load_feedback_by_project(self, project_id: str) -> List[FeedbackInput]:
        feedbacks = self._read_all()
        project_feedbacks = [f for f in feedbacks if f.get("project_id") == project_id]
        return [FeedbackInput.model_validate(f) for f in project_feedbacks]

    def list_all_feedback(self) -> List[FeedbackInput]:
        feedbacks = self._read_all()
        return [FeedbackInput.model_validate(f) for f in feedbacks]

    def clear(self) -> None:
        self._write_all([])

global_feedback_store = FeedbackStore()
