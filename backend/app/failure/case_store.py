import os
import json
from typing import List, Dict, Any, Optional
from .schemas import FailureCase

class FailureCaseStore:
    """
    负责沉淀并持久化失败案例 (Failure Case) 至本地 JSON 文件。
    并支持通过 replay_failure_case 方法重放执行流。
    """
    def __init__(self, file_path: Optional[str] = None):
        if file_path:
            self.file_path = file_path
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.file_path = os.path.normpath(os.path.join(current_dir, "..", "..", "storage", "failure_cases.json"))
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

    def save_failure_case(self, case: FailureCase) -> None:
        cases = self._read_all()
        # 避免保存重复的 case_id
        cases = [c for c in cases if c.get("case_id") != case.case_id]
        cases.append(case.model_dump())
        self._write_all(cases)

    def load_failure_case(self, case_id: str) -> Optional[FailureCase]:
        cases = self._read_all()
        for c in cases:
            if c.get("case_id") == case_id:
                return FailureCase.model_validate(c)
        return None

    def list_failure_cases(self) -> List[FailureCase]:
        cases = self._read_all()
        return [FailureCase.model_validate(c) for c in cases]

    def replay_failure_case(self, case_id: str) -> Any:
        from .replay import replay_case
        return replay_case(case_id)

    def clear(self) -> None:
        self._write_all([])

global_failure_case_store = FailureCaseStore()
