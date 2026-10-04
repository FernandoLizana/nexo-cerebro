# P6 — Overview

**Phase:** P6 · **Theme:** Cognitive QA Metrics + Failure Taxonomy + Certificates

Pipeline:

```text
RawRunTrace → normalize_events → FailureClassifier → episodes → MetricEngine → certificates → reports
```

Entry points:

- `analyze_run(runtime, world=...)` — live capture + analyze
- `analyze_run_file(path)` — offline, no browser
- `analyze_raw_trace(raw, output_dir=...)` — writes JSON + Markdown reports

All scores labeled **simulation-derived; not human-calibrated**.
