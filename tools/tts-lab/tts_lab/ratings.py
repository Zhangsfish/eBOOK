"""The protocol's fixed weights. No imputed listening scores or ranking."""
from decimal import Decimal
from .core import LabError

CRITERIA = (
    ('comfort', '长时间耐听、柔和与温暖', 30),
    ('naturalness', '自然韵律、语气与停顿', 25),
    ('pronunciation', '普通话、姓名地名与数字发音', 15),
    ('dialogue', '对话与克制的情绪表达', 10),
    ('continuity', '相邻合成块的声线一致性', 10),
    ('clarity', '清晰度与无伪影', 5),
    ('reliability', '延迟与运行可靠性', 5),
)


def weighted_score(scores):
    if any(scores.get(name) in (None, '') for name, _, _ in CRITERIA):
        return None
    total = Decimal(0)
    for name, _, weight in CRITERIA:
        try:
            value = Decimal(str(scores[name]))
        except Exception:
            raise LabError('Scores must be integers from 1 to 5.') from None
        if not value.is_finite() or value != value.to_integral_value() or not 1 <= value <= 5:
            raise LabError('Scores must be integers from 1 to 5.')
        total += value * weight / 100
    return total
