# Asset and validation guide

This guide distinguishes present, missing, incompatible, historical, and newly generated artifacts.

## Current status in this repository clone

### Present

- `README.md`
- `CONTRIBUTING.md`
- `docs/environment.md`
- `docs/asset_validation_guide.md`
- `model/reproduce_template.ipynb` (new, unexecuted scaffold)
- `tools/check_research_assets.py`

### Missing expected research assets

- `dataset/`
- `dataset_code/`
- `model/model.ipynb`
- `model/scaler.pkl`
- `model/embedded/`

### Historical vs new artifacts policy

- Historical: owner-supplied original notebook and saved artifacts.
- New: any future rerun outputs under `runs/<run_id>/`.
- Do not overwrite historical assets.

## Validation commands

```bash
python tools/check_research_assets.py --repo-root .
```

Optional strict hash check once original notebook is uploaded:

```bash
python tools/check_research_assets.py \
  --repo-root . \
  --expected-original-notebook-sha256 <sha256>
```

## Checker scope

The checker performs lightweight, non-training checks:

1. Notebook JSON format check (`model/model.ipynb`).
2. Optional original notebook hash verification.
3. Dataset feature and label contract check for `dataset/master_dataset_unseen_seed2952.csv`.
4. Optional ONNX shape inspection for files in `model/embedded/`.

Checks that cannot run because assets/dependencies are unavailable are explicitly reported as `SKIP`.
