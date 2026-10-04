# Third-party content and redistribution

**Purpose:** inventory of local study materials that must **not** ship in the public GitHub reproducible artifact by default, plus how to obtain fixtures for local lab use.

The release builder (`scripts/build_release_artifact.py`) excludes:

- all `*.pdf` (suffix)
- the entire `data/library/` tree (prefix)
- runtime/private dirs (`data/brain_state/`, gateway certs, tokens, etc.)

First-party **synthetic curriculum JSON** under `data/curriculum/` **is** allowed in the artifact.

---

## `data/library/` (local only)

**Historical note:** Through commit `a6ee9674` (audit baseline on `nexo-collective-swarm`), the five third-party study PDFs under `data/library/` were tracked in git. They remain in that history. They were removed from the index (not deleted from disk) so a public tree no longer stages them; rewriting history is an owner decision outside automated remediation.

These files may exist on a developer machine after downloading study PDFs. They are **not** NEXO-owned redistributables.

| File | Role | Redistribution |
|------|------|----------------|
| `manual-neurologia-para-el-interno-y-medico-general-2-1.pdf` | Clinical neurology handbook (third-party medical PDF) | **Must NOT** appear in the public GitHub ZIP |
| `Anatomia_Humana_2022_UCadiz.pdf` | Anatomy textbook PDF (third-party) | Do not ship in artifact |
| `Biological-Psychology-Revised-Edition-1742238833.pdf` | Biopsychology PDF (third-party) | Do not ship in artifact |
| `Brain_Facts_Book_2018.pdf` | Brain Facts book PDF (third-party) | Do not ship in artifact |
| `Mi-primer-libro-del-cerebro.pdf` | Children's brain book PDF (third-party) | Do not ship in artifact |
| `_extract_*.txt` | Local text extracts derived from the above | Lab-only; excluded with `data/library/` |
| `test-lib*.txt` | Tiny first-party smoke fixtures | Prefer keeping out of public ZIP with the library tree; use curriculum JSON for CI |

If a PDF is missing, autonomy/shelf demos that expect it will skip or fail locally — that is expected. Do not commit binary PDFs to make CI green.

### How to obtain fixtures (owner lab)

1. Acquire each PDF only under a license that permits **personal/lab** use (publisher, open educational resource, or fair-use local copy as applicable in your jurisdiction).
2. Place files under `data/library/` with the names above (or update extract scripts to match).
3. Optionally regenerate text extracts used by shelf/phrase demos (see `scripts/prove_pdf_autonomy.py` and library helpers in the repo).
4. Never add these PDFs to git staging for a public release branch unless legal review explicitly allows it.

---

## `data/curriculum/` (first-party / derived manifests — ship OK)

Synthetic or owner-authored section manifests used by tests and demos. These are **not** the medical PDFs themselves.

| Path | Notes |
|------|--------|
| `sections.json` | Top-level curriculum index |
| `_toc_scan.json` | TOC scan helper |
| `anatomy_humana_2022_manifest.json` | Manifest/fixture (no embedded PDF binary) |
| `brain_facts_manifest.json` | Manifest/fixture |
| `biopsych_phases/sections.json` | Phase sections |
| `clinical_neurology_uddl/sections.json` | Clinical sections fixture |
| `infant_brain/sections.json` | Infant-brain sections |

These remain in `REQUIRED_PREFIXES` for the release artifact (`data/curriculum/`).

---

## Artifact policy reminder

```bash
python scripts/build_release_artifact.py
```

Post-build `scan_artifact_for_secrets` also flags any accidental `*.pdf` or `data/library/` path inside the ZIP as a packaging error.

See also: [`NEXO_INSTALL.md`](NEXO_INSTALL.md), [`SECURITY.md`](../SECURITY.md).
