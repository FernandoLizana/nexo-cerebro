# P8 — Overview

P8 adds **controlled environmental perturbations** with **paired baseline vs perturbed** design:

```text
same task + same persona + same seed
        BASELINE  vs  PERTURBED
              ↓           ↓
            P6 run      P6 run
              └─────┬─────┘
                    ↓
              PairedChaosDelta
```

**Module:** `nexo_qa/chaos/` · **Phase:** P8 · **Version:** `0.8.0-p8`

Perturbations affect the **environment only** — not persona traits, WM, or decision scores directly.
