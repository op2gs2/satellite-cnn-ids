# Environment and dependency guidance

This repository currently does not contain the original experiment notebook (`model/model.ipynb`) or dataset/model artifacts, so exact historical package versions cannot yet be extracted from source.

## What is verified in this PR

- `tools/check_research_assets.py` runs with Python standard library only.
- No lockfile is introduced in this PR.

## Core notebook dependencies (for rerun workflow once notebook is provided)

Install as needed for notebook-based preprocessing, training, and evaluation:

- `jupyter`
- `numpy`
- `pandas`
- `scikit-learn`
- `torch`
- `matplotlib`
- `seaborn`
- `onnx`

## Optional dependencies

### Optional host-side ONNX/OpenCV numerical comparison

- `opencv-python`

### Optional ONNX runtime checks

- `onnxruntime`

### Optional dataset-generation pipeline dependencies

These are environment-specific and depend on the dataset scripts that will be uploaded under `dataset_code/`.
Typical requirements may include:

- Linux tooling (`tcpdump`, Docker, scenario tooling)
- Python packages used by capture/feature-extraction scripts

Do not assume native Windows compatibility for historical capture scripts unless those scripts explicitly support it.

## Practical install example

```bash
python -m pip install jupyter numpy pandas scikit-learn torch matplotlib seaborn onnx
python -m pip install opencv-python onnxruntime
```

Treat this as a starting point until imports are verified directly from the uploaded original notebook.
