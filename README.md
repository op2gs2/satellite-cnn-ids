# Satellite CNN IDS

**Repository name:** `satellite-cnn-ids`

This repository accompanies *A Lightweight CNN-Based Intrusion Detection Architecture for Satellite Onboard Computers: A Simulation-Based Study*, planned for presentation at **MobiSec 2026**. The study uses a lightweight CNN to detect intrusions from CCSDS and CSP/CAN traffic features. The repository contains dataset preparation scripts, a documented training notebook with saved results, and ONNX and input-data artifacts for embedded integration.

Start with [`model/model.ipynb`](model/model.ipynb). It contains preprocessing, CNN training, test evaluation, confusion-matrix visualization, ONNX export, and validation-input generation in one notebook. Its saved outputs are historical results; opening the notebook does not rerun an experiment.

## Repository layout

```text
satellite-cnn-ids/
├── dataset/
│   ├── pcap/                              # Captured and generated packet files
│   ├── csv/                               # Per-scenario feature tables
│   ├── master_dataset.csv                 # Earlier, smaller feature schema
│   ├── master_dataset_raw_seed*.csv
│   ├── master_dataset_unseen_seed*.csv     # Feature-rich datasets
│   └── external_unseen_seed_list.txt
├── dataset_code/
│   ├── main.py                            # Historical collection/build pipeline
│   ├── cosmos_runner.py                   # COSMOS execution and packet capture
│   ├── hybrid_builder.py                  # Hybrid traffic generation
│   ├── feature_extractor.py               # PCAP-to-feature conversion
│   ├── merge_and_label.py                  # Filename-based labels and CSV merge
│   ├── validate_hybrid.py                 # Earlier CSV-schema validator
│   ├── augmentation/                      # Dataset augmentation
│   ├── can_attack/                        # Modules imported by hybrid_builder
│   ├── csp_over_can/                       # Additional copies of CAN modules
│   ├── scripts/                           # COSMOS scenario scripts
│   └── ccsds/                             # Additional scripts and augmentation
└── model/
    ├── model.ipynb                         # Main experiment and saved outputs
    ├── scaler.pkl                         # Supplied standardization artifact
    └── embedded/
        ├── final_stm32.onnx               # Earlier graph; see external-data note below
        ├── final_stm32.onnx.data          # External weights; filename reference needs alignment
        ├── final_stm32_clean.onnx         # Self-contained graph with a 30 × 23 input
        ├── satellite_real_data.npz
        ├── satellite_real_data_30.npz
        ├── satellite_real_input_only.npz
        ├── satellite_real_labels.npy
        ├── satellite_real_metadata.json
        └── test_samples.h
```

## Download the dataset with Git LFS

CSV files are configured for Git Large File Storage (Git LFS). Install Git and [Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage), then open a new terminal and run:

```bash
git --version
git lfs version
git lfs install
```

The dataset files and their LFS objects must be published on the checked-out branch before they can be downloaded. Configuring `.gitattributes` alone does not upload the data.

### Clone the repository and download all published LFS data

Run these commands from the directory where you want to keep the repository:

```bash
git clone https://github.com/op2gs2/satellite-cnn-ids.git
cd satellite-cnn-ids
git lfs pull --include="" --exclude=""
```

Cloning with Git LFS enabled normally downloads the LFS content automatically. The final command retrieves any remaining objects for the checked-out revision and replaces their local pointer files. The empty include and exclude options clear download filters for this command. See the [Git LFS pull documentation](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-pull.adoc).

### Download only the notebook's training CSV

For a new clone, use this alternative to skip automatic LFS downloads and request only the CSV used by the notebook:

```bash
git -c lfs.fetchexclude="*" clone https://github.com/op2gs2/satellite-cnn-ids.git
cd satellite-cnn-ids
git lfs pull --include="dataset/master_dataset_unseen_seed2952.csv" --exclude=""
```

Choose either this clone sequence or the full-download sequence above. The `-c` setting applies only to that clone command; it does not change your global configuration. Files stored in ordinary Git are still downloaded during cloning. The [LFS filter documentation](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-smudge.adoc) explains how download exclusions work.

### Download data in an existing clone

From the existing repository root, run:

```bash
git lfs install
git lfs pull --include="" --exclude=""
```

For just the training CSV, use the selective `git lfs pull --include=...` command above instead. `git lfs pull` downloads data for the current revision; it does not update your Git branch. If the dataset was added in a newer commit, first update your branch with `git pull --ff-only` after committing or stashing your local changes. A branch update can also download newly referenced LFS files.

### Check the download

List the LFS files and their sizes:

```bash
git lfs ls-files --size
```

An asterisk (`*`) after a file's object ID indicates full content in the working tree; a minus (`-`) indicates a pointer. An empty list means no LFS files were found in the checked-out revision, not that the dataset was downloaded. See the [Git LFS file-list documentation](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-ls-files.adoc).

Before training, confirm that `dataset/master_dataset_unseen_seed2952.csv` exists and contains a CSV header. In Windows PowerShell:

```powershell
Get-Content -LiteralPath .\dataset\master_dataset_unseen_seed2952.csv -TotalCount 1
```

A line beginning with `version https://git-lfs.github.com/spec/v1` is an LFS pointer, not training data. Fetch the file with the selective download command before opening it in pandas.

If a file is absent from the branch, the maintainer must publish it first. Missing-object, authentication, or storage/bandwidth errors must be resolved before retrying the download; do not substitute a pointer file or another dataset. Once the required CSV is present, continue with the notebook setup below.

## Run the notebook

### 1. Prepare a Python environment

The notebook imports PyTorch, NumPy, pandas, scikit-learn, joblib, Matplotlib, IPython, and ONNX. JupyterLab provides the notebook interface. The repository does not include a pinned dependency file or a complete record of the original environment.

From the repository root, a Windows PowerShell setup is:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install jupyterlab ipykernel torch numpy pandas scikit-learn joblib matplotlib onnx
.\.venv\Scripts\python.exe -m ipykernel install --user --name satellite-cnn-ids --display-name "Satellite CNN IDS"
```

These commands provide an unpinned starting environment. They have not been used here to reproduce the saved experiment. The notebook selects CUDA when available and otherwise uses the CPU; it does not require a GPU to select a device.

### 2. Keep the saved experiment and create a new run

Open `model/model.ipynb` to inspect the original code and results. For a new experiment, choose an unused run-directory name and copy the notebook there. The notebook writes `scaler.pkl` and an `embedded/` directory relative to the kernel's working directory, so a separate run directory also keeps the supplied artifacts intact.

From the repository root:

```powershell
New-Item -ItemType Directory -Path .\runs\experiment_01
Copy-Item -LiteralPath .\model\model.ipynb -Destination .\runs\experiment_01\model.ipynb
.\.venv\Scripts\python.exe -m jupyterlab --notebook-dir .\runs\experiment_01
```

Select the **Satellite CNN IDS** kernel. In the copied notebook, change `csv_path` in **Set the input path and experiment options** to:

```python
csv_path = "../../dataset/master_dataset_unseen_seed2952.csv"
```

This relative path assumes the kernel runs from `runs/experiment_01`. If using a different location, set an absolute path to the same CSV. The original notebook contains a machine-specific absolute path that must be updated in the working copy.

The filename contains `unseen`, but this notebook splits that file into training, validation, and test sets. This run therefore does not constitute an independent evaluation on a wholly unseen dataset.

Clear outputs **only in the working copy**, restart its kernel, and run the cells from top to bottom. This prevents old results from being mistaken for results from a partial new run.

### 3. Follow the experiment sequence

| Stage | What the notebook does |
| --- | --- |
| Configuration | Sets the input CSV, seed, window length, split ratios, and export options. |
| Preprocessing | Sorts by time when available, combines the two labels, handles payload-length strings, and selects 23 features. |
| Splitting | Builds blocks of up to 1,000 rows within the available source/run and label groups, then stratifies blocks into training, validation, and test sets. |
| Standardization | Converts features to numbers, replaces missing values with zero, fits `StandardScaler` on training rows, and transforms all splits. |
| Windowing | Builds 30-row windows within each block, using stride 1 and the last row's label. |
| Training | Trains the CNN and retains the weights with the highest validation macro-F1. |
| Evaluation | Reports combined and per-protocol metrics, classification reports, and confusion matrices. |
| ONNX export | Exports the current model, removes `Reshape` `allowzero` attributes if present, and runs the ONNX format checker. |
| Visualization | Plots the 25-class test confusion matrix. |
| Validation inputs | Saves 100 standardized input windows and generates C input arrays for 25 classes. |

The notebook does not save a PyTorch `.pt` or `.pth` checkpoint. Export depends on the trained `model` still being present in the kernel.

## Data and model contract

### Labels

Both `CCSDS_Label` and `CAN_Label` use integer values from 0 to 4. The model predicts 25 combinations:

```python
Combined_Label = 5 * CCSDS_Label + CAN_Label
predicted_ccsds = predicted_class // 5
predicted_can = predicted_class % 5
```

The dataset scripts define the label names as follows:

| ID | CCSDS scenario | CAN context |
| --- | --- | --- |
| 0 | `normal_ops` | `none` |
| 1 | `command_flood` | `can_flood` |
| 2 | `data_injection` | `can_spoofing` |
| 3 | `storage_exhaustion` | `can_dos` |
| 4 | `defence_impairment` | `can_replay` |

The legacy context name `can_flood` invokes `attack_fuzz.generate_fuzzing` in `hybrid_builder.py`.

### Feature order

The CSV must already contain these 23 features, in addition to the two label columns. The notebook selects them in this order; it does not derive the missing engineered features from raw packets.

```text
CCSDS_APID, CCSDS_DataLen,
CSP_Priority, CSP_Source, CSP_Dest, CSP_DPort, CSP_SPort, CSP_Flags,
Payload_Len, Time_Delta_Log, Flags_Change, Payload_Diff, APID_Count,
Global_Time_Delta_Log, APID_Time_Delta_Log, APID_Changed_Roll10,
CCSDS_DataLen_AbsDiff, CCSDS_SeqCount_AbsDiff, Packet_Rate_Roll10_Log,
CSP_Nonzero_Roll10, CSP_Route_Changed_Roll10,
Payload_Len_RollStd10, P_Entropy_Log_RollStd10
```

`dataset/master_dataset_unseen_seed2952.csv` contains the required columns. The earlier `dataset/master_dataset.csv` lacks several required features and cannot be substituted directly. Preserve available provenance fields such as `Source_File`, `Trace_ID`, and `Run_ID` when preparing replacement data because they affect block construction.

### CNN and training settings

| Item | Current notebook |
| --- | --- |
| Input | FP32 tensor `(batch, 30, 23)` |
| First convolution | 1 → 8 channels, kernel `(1, 5)`, padding `(0, 2)`, ReLU |
| First pooling | Max pooling `(2, 1)` |
| Second convolution | 8 → 16 channels, kernel `(3, 3)`, padding `(1, 1)`, ReLU |
| Second pooling | Max pooling `(2, 1)` |
| Classifier | Flatten → 64 units → ReLU → 25 logits |
| Parameters | 167,769 |
| Seed / batch size | 42 / 64 |
| Split targets | 70% training, 10% validation, 20% test by blocks |
| Optimizer | Adam, learning rate `0.001` |
| Loss | Focal loss computed from class-weighted cross-entropy; `alpha=1`, `gamma=2` |
| Training limit | 15 epochs; early stopping enabled with patience 5 |
| Weight selection | Best validation macro-F1, including when early stopping is disabled |

There is no teacher model or knowledge-distillation loss in the current notebook. `StudentSTFake2DCNN` and the notebook's legacy export filename retain the word `student`.

## Saved results

The notebook retains the following historical test results. They have not been regenerated as part of documenting this repository.

| Metric | Saved value |
| --- | ---: |
| Test windows | 292,271 |
| Combined accuracy | 99.3174% |
| Macro-F1 | 99.3964% |
| Weighted F1 | 99.3175% |
| CCSDS accuracy | 99.3219% |
| CAN accuracy | 99.9949% |

The saved log contains 15 training epochs and restoration of the best validation weights. The displayed total training time is **549.14 seconds**, a host training measurement, not an MCU inference-latency measurement.

These values differ from the manuscript's 99.4991% accuracy and 99.4990% macro-F1. Use the actual experiment record when revising the manuscript. A new run can also differ with changes in data, dependencies, hardware, or training settings.

## ONNX and embedded artifacts

The current `model/embedded/` directory contains the nine files listed above. The two ONNX graphs have different input contracts and should not be treated as interchangeable versions of the same model.

### Current files and compatibility

Static inspection of the current files found:

| File in `model/embedded/` | Observed contract or status |
| --- | --- |
| `final_stm32.onnx` | Opset 18; input `(1, 10, 20)`; output `(1, 25)`. Its external-weight references still point to `final_student_stm32.onnx.data`, which is absent from this folder. |
| `final_stm32.onnx.data` | External-weight file present under the new name. The ONNX graph still refers to the old filename, so this reference is unresolved. |
| `final_stm32_clean.onnx` | Self-contained opset-11 graph; input `(1, 30, 23)`; output `(1, 25)`; no external-data references. Its input dimensions match the current notebook's feature and window configuration. |
| `satellite_real_data.npz`, `satellite_real_data_30.npz` | Key `input`; FP32 arrays with shape `(100, 30, 23)`. |
| `satellite_real_input_only.npz` | FP32 input shape `(100, 20, 30)`; incompatible with the current notebook's `(1, 30, 23)` model input. |
| `satellite_real_labels.npy` | Int64 array with shape `(100,)`; association with the current input files has not been established. |
| `satellite_real_metadata.json` | Describes 30 features and shape `(100, 30, 30)`; does not describe the current 23-feature inputs. |
| `test_samples.h` | C sample input arrays and label information for validation; not generated CNN inference firmware. |

Renaming an external-weight file does not update the filename stored inside an ONNX graph. Before using `final_stm32.onnx`, its stored reference must be updated to the accompanying filename, or the referenced filename must be restored. Its `(1, 10, 20)` input also differs from the current notebook's input. Make any reference correction in a working copy of the artifacts.

Use the dimensions above to select compatible inputs. Matching dimensions alone do not prove that a model was trained with the supplied scaler or that its weights produced the notebook's saved metrics.

### Filenames generated by the preserved notebook

The original notebook has not been changed to match the reorganized folder. After training, its export and validation-input cells are configured to write:

- `embedded/final_stm32.onnx`: a new opset-11 export of the current in-memory model, with input `(1, 30, 23)` and output `(1, 25)`. This differs from the opset-18 graph currently supplied under that filename.
- `embedded/final_student_stm32_clean.onnx`: the notebook's original filename for the graph after the compatibility edit and ONNX format check. The corresponding filename used in the current folder layout is `final_stm32_clean.onnx`.
- `embedded/satellite_real_data_30.npz`: key `input`, FP32 shape `(100, 30, 23)`, four test windows per class. Labels remain in `y_val_stm` in memory and are not saved by this cell.
- `embedded/test_samples.h`: one standardized 30 × 23 input array per class, with label and feature-order information.

For a future run that uses the current naming convention, change the following assignment only in a working copy of the notebook:

```python
clean_onnx_path = "./embedded/final_stm32_clean.onnx"
```

Run the working copy in a separate run directory so that a new export does not overwrite the supplied artifacts. Generate the model, scaler, and validation inputs together, then check their feature order, dimensions, and provenance.

The **saved ONNX cell output reports that export was skipped because `onnx` was missing**. Install ONNX in the selected kernel and check for `onnx_export_status == "completed"` after a new run. Existing ONNX files alone do not establish that the saved training run produced them.

ONNX format validation does not run inference or establish numerical equivalence. The current notebook does not include the manuscript's 100-sample OpenCV–PyTorch comparison, ONNX test-set evaluation, STM32 firmware integration, or board timing and memory measurements. Those require separate execution and records. The folder contains no complete STM32 firmware project or board measurement logs.

## Dataset generation scripts

The dataset-generation workflow builds on the scripts accompanying [*CubeSat cybersecurity dataset for intrusion detection (CuCD-ID): Labelled NOS3/cFS telemetry (raw + augmented) with COSMOS reproduction scripts*](https://www.sciencedirect.com/science/article/pii/S2352340926001514). The scripts were converted for compatibility with the cFS version used in this project.

Original work: Yasamin Fayyaz, Seyedeh Negar Afrasiabi, Li Yang, and Khalil El-Khatib. *Data in Brief*, 65, 112598 (2026). [DOI: 10.1016/j.dib.2026.112598](https://doi.org/10.1016/j.dib.2026.112598).

The supplied CSV files allow the notebook workflow to start without capturing new traffic. The generation code is retained for inspecting and adapting the original pipeline:

1. `cosmos_runner.py` runs scenario scripts in a COSMOS container and captures UDP traffic with `tcpdump`.
2. `hybrid_builder.py` uses the `can_attack/` modules to generate hybrid packet files.
3. `feature_extractor.py` extracts header, payload, timing, and rolling features from PCAP files.
4. `main.py` or `merge_and_label.py` assigns labels from filenames and merges feature tables.
5. `augmentation/augmentation_script.py` provides an augmentation command with `--input`, `--output`, and `--seed` options.

The Python dependencies for this code include NumPy, pandas, SciPy, Scapy, and tqdm. The capture stage also requires a configured Linux/COSMOS environment, Docker, `tcpdump`, and the scenario targets used by the scripts. `cosmos_runner.py` imports Linux `fcntl` and assumes the container name `cosmos-openc3-operator-1`. Several files retain absolute paths under `/home/ubuntu/Desktop/hybrid_ids_project`; update them to the intended environment before use.

The current `main.py` loops over four CAN attack contexts and does not include a `none` context in that loop. It is not a complete one-command reconstruction of every supplied 25-class dataset. Also, `validate_hybrid.py` enforces an older exact column set, so its schema check is not suitable for the feature-rich training CSV without adaptation.

## License

No license file is included in the supplied folder. Reuse and redistribution terms have not been specified.

## Citation

The paper is planned for presentation at **MobiSec 2026**. Use the provisional BibTeX entry below, adding the author list and final publication details when available.

Add this entry to your bibliography file, such as `references.bib`:

```bibtex
@misc{satellite_cnn_ids_mobisec2026,
  title = {{A Lightweight CNN-Based Intrusion Detection Architecture for Satellite Onboard Computers: A Simulation-Based Study}},
  year = {2026},
  note = {Planned for presentation at MobiSec 2026}
}
```

With that bibliography file included in your LaTeX document, cite the paper using:

```latex
\cite{satellite_cnn_ids_mobisec2026}
```
