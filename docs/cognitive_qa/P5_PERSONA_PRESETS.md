# P5 — Persona Presets

Engineering profiles — **NOT human-calibrated**.

| Preset | Purpose | Key traits | Does NOT claim |
|--------|---------|------------|----------------|
| baseline | P4-equivalent defaults | all 0.5 / WM=4 | Represents any human population |
| low_wm | Memory-limited profile | WM=2 | Clinical memory impairment |
| high_distractibility | Salience sensitivity | distractibility=0.88 | ADHD |
| risk_averse | Caution under risk | risk_aversion=0.9 | Anxiety disorder |
| impatient | Low patience, high impulsivity | patience=0.2, impulsivity=0.85 | Age or personality type |
| fatigued | Elevated fatigue | initial_fatigue=0.55 | Sleep deprivation diagnosis |
| novice_digital | Low UI literacy | digital_literacy=0.15 | "Boomer" or age cohort |
| expert_digital | High UI literacy | digital_literacy=0.9 | Power user stereotype |

Location: `configs/nexo_qa/personas/*.yaml`

Composite personas: combine traits in YAML with unique `persona_id`.
