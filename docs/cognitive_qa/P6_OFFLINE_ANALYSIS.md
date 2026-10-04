# P6 — Offline Analysis

```python
from nexo_qa.analysis import analyze_run_file

result = analyze_run_file("path/to/raw_trace.json", output_dir="artifacts/run_analysis")
```

- Raw JSON immutable
- Derived reports written to output_dir
- No browser rerun required when trace has sufficient data

See `nexo_qa/analysis/offline.py`.
