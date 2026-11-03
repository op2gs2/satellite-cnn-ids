# satellite-cnn-ids

Repository for the research project **A Lightweight CNN-Based Intrusion Detection Architecture for Satellite Onboard Computers: A Simulation-Based Study**.

Status: planned for presentation at **MobiSec 2026**.

## Current repository state (verified in this clone)

At the time of this PR, the expected research assets are **not yet present** in the repository tree. The following expected paths are currently missing in this clone:

- `dataset/`
- `dataset_code/`
- `model/model.ipynb` (original historical notebook)
- `model/scaler.pkl`
- `model/embedded/`

This PR prepares a notebook-centered structure and validation workflow without fabricating historical results or replacing the original experiment notebook.

## Project purpose

This project studies a lightweight CNN-based intrusion detector using features derived from CCSDS and CSP/CAN traffic. The intended workflow is:

1. Prepare simulation-derived tabular data.
2. Run preprocessing and block/window construction in a notebook.
3. Train and evaluate a CNN model.
4. Export ONNX artifacts.
5. Prepare host-side validation inputs for later embedded validation work.

## Repository layout

- `README.md` - project overview and run guidance.
- `CONTRIBUTING.md` - contribution boundaries for preserving research records.
- `docs/asset_validation_guide.md` - asset status matrix and compatibility notes.
- `docs/environment.md` - environment and dependency guidance.
- `model/reproduce_template.ipynb` - unexecuted working notebook scaffold.
- `tools/check_research_assets.py` - lightweight checks for notebook/data/ONNX contracts.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install only what you need:

- For repository checks only: no third-party package is required.
- For notebook reruns and model work: follow `docs/environment.md`.

## Notebook-centered workflow policy

- Keep the experiment integrated in notebooks.
- Preserve `model/model.ipynb` byte-for-byte when it is provided.
- Do not rerun or rewrite the historical notebook in place.
- Use a separate working copy for new runs and clearly mark execution status.
- Do not overwrite supplied historical artifacts by default.

## Data and model contract to preserve

When the original assets are uploaded, the notebook workflow should explicitly preserve:

- 23 ordered input features and sequence shape `(batch, 30, 23)`.
- `Combined_Label = 5 * CCSDS_Label + CAN_Label` with class range `0..24`.
- Block-aware windowing and split policy as implemented in the source notebook.
- Training policy (batch size, optimizer, epoch limit, early stopping behavior) from the source notebook.
- Separate reporting of historical notebook results vs new executions.

## Lightweight validation checks

Run:

```bash
python tools/check_research_assets.py --repo-root .
```

The checker reports `PASS`, `FAIL`, or `SKIP` for:

- original notebook presence and JSON format,
- optional original hash matching,
- required dataset columns and label ranges,
- optional ONNX input/output shape compatibility.

Checks requiring missing assets or missing optional dependencies are marked `SKIP` with a reason.

## Evidence and limitation notes

- A filename containing `unseen` does not by itself prove external independence.
- Host-side ONNX/PyTorch numerical agreement is not the same as classification accuracy.
- ONNX graph checks are not STM32 hardware validation.
- Existing historical values should be treated as owner-provided context until the original notebook and saved outputs are available in this repository.

## Next steps after assets are uploaded

1. Import the original `model/model.ipynb` without modification.
2. Record original file hash before and after any repository updates.
3. Add one working notebook copy (for example `model/reproduce.ipynb`) with clear inherited-vs-new execution labeling.
4. Run dataset/feature contract checks and ONNX compatibility checks.
5. Execute new runs into unique `runs/<run_id>/` directories only.

## Citation

Paper title: **A Lightweight CNN-Based Intrusion Detection Architecture for Satellite Onboard Computers: A Simulation-Based Study**  
Status note: Planned for presentation at **MobiSec 2026**.

```bibtex
@misc{satellite_cnn_ids_mobisec2026,
  title = {{A Lightweight CNN-Based Intrusion Detection Architecture for Satellite Onboard Computers: A Simulation-Based Study}},
  year = {2026},
  note = {Planned for presentation at MobiSec 2026.}
}
```

```latex
\cite{satellite_cnn_ids_mobisec2026}
```
