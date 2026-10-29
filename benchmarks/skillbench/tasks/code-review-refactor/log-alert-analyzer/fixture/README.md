# logwatch

`logwatch` parses structured `key=value` application log lines, computes per-service latency and error metrics, classifies service health, and renders Markdown alert summaries.

## Layout

- `logwatch/analyzer.py` — `analyze_log_lines`, `filter_critical_events`, and `render_markdown_summary`.
- `tests/test_analyzer.py` — `unittest` suite (`python -m unittest discover -s tests -v`).
