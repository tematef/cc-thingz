"""logwatch: structured log parsing and service health reporting."""

from .analyzer import (
    analyze_log_lines,
    filter_critical_events,
    render_markdown_summary,
)

__all__ = [
    "analyze_log_lines",
    "filter_critical_events",
    "render_markdown_summary",
]
