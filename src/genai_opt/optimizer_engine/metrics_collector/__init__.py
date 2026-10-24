"""Optional helpers that summarize iteration metadata you already hold.

The engine does not call these; see
:class:`~genai_opt.optimizer_engine.metrics_collector.metrics_collector.MetricsCollector`
for how they relate to experiment controllers.
"""

from genai_opt.optimizer_engine.iteration_metadata import IterationMetadata
from genai_opt.optimizer_engine.metrics_collector.metrics_collector import (
    MetricsCollector,
)

__all__ = ["IterationMetadata", "MetricsCollector"]
