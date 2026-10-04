# Swarm Simulator — documented load curves (S11)

These envelopes are **planning targets** for the in-process discrete-event
engine (`services/simulator`). They are **not** measurements of real
multi-device or internet networking.

| Logical nodes | Beings / node | Horizon | Expected peak queue | Memory budget |
|--------------:|--------------:|--------:|--------------------:|--------------:|
| 10 | 2 | 50 | 64 | 2 MB |
| 100 | 2 | 100 | 512 | 8 MB |
| 1 000 | 2 | 50 | 4 096 | 64 MB |
| 10 000 | 1 | 20 | 16 384 | 256 MB |

Source of truth in code: `services.simulator.metrics.load_curve_table()`.

**Rules**

- One OS process hosts all logical nodes.
- No sockets / no subprocess fan-out.
- Do not treat simulator throughput as proof that a real lab is ready (that is S15).
