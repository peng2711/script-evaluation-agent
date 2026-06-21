import time
from typing import Any, Dict, Optional

class SimpleCache:
    """
    轻量级本地内存缓存，支持时间戳 TTL 过期校验与命中/未命中统计。
    """
    def __init__(self):
        # 存储结构: {key: (value, expire_time)}
        self._cache: Dict[str, tuple] = {}
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expire_time = self._cache[key]
            if expire_time is None or expire_time > time.time():
                self._hit_count += 1
                # 同步记录至当前 Context 中的 Trace 记录器（若存在）
                from ..observability.trace import active_trace_recorder
                recorder = active_trace_recorder.get()
                if recorder and hasattr(recorder, "record_cache_hit"):
                    recorder.record_cache_hit()
                return value
            else:
                # 键已过期，主动从内存中清理
                del self._cache[key]

        self._miss_count += 1
        # 同步记录至当前 Context 中的 Trace 记录器（若存在）
        from ..observability.trace import active_trace_recorder
        recorder = active_trace_recorder.get()
        if recorder and hasattr(recorder, "record_cache_miss"):
            recorder.record_cache_miss()
        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        expire_time = time.time() + ttl_seconds if ttl_seconds is not None else None
        self._cache[key] = (value, expire_time)

    def clear(self):
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0

    def stats(self) -> Dict[str, Any]:
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total) if total > 0 else 0.0
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "size": len(self._cache)
        }

# 全局单例缓存实例
global_cache = SimpleCache()
