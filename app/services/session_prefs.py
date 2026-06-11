"""P1修复: E→B数据回路。Agent会话级偏好缓存，本次对话内的反馈立即影响后续推荐。"""

_session_prefs: dict[str, list[str]] = {}  # trace_id → [tag1, tag2, ...]


def add_session_prefs(trace_id: str, tags: list[str]):
    """评分后立即更新会话偏好"""
    if trace_id not in _session_prefs:
        _session_prefs[trace_id] = []
    for t in tags:
        if t not in _session_prefs[trace_id]:
            _session_prefs[trace_id].append(t)


def get_session_prefs(trace_id: str) -> list[str]:
    return _session_prefs.get(trace_id, [])


def clear_session(trace_id: str):
    _session_prefs.pop(trace_id, None)
