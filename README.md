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
        ├── final_stm32.onnx
        ├── final_student_stm32_clean.onnx
        ├── final_student_stm32.onnx        # Different, earlier input contract
        ├── *.onnx.data
        ├── satellite_real_data_30.npz
        ├── satellite_real_data.npz
        ├── satellite_real_input_only.npz
        ├── satellite_real_labels.npy
        ├── satellite_real_metadata.json
        └── test_samples.h
```

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

There is no teacher model or knowledge-distillation loss in the current notebook. `StudentSTFake2DCNN` and some `student` filenames are retained identifiers.

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

After training, the export and validation-input cells write:

- `embedded/final_stm32.onnx`: opset 11, fixed input `(1, 30, 23)`, output `(1, 25)`.
- `embedded/final_student_stm32_clean.onnx`: the exported graph after the compatibility edit and ONNX format check.
- `embedded/satellite_real_data_30.npz`: key `input`, FP32 shape `(100, 30, 23)`, four test windows per class. Labels are held in `y_val_stm` in memory and are not saved by this cell.
- `embedded/test_samples.h`: one standardized 30 × 23 input array per class, with label and feature-order information. This is sample data for a C program, not generated CNN inference code.

The **saved ONNX cell output reports that export was skipped because `onnx` was missing**. Install ONNX in the selected kernel and check for `onnx_export_status == "completed"` after a new run. Existing ONNX files alone do not establish that the saved training run produced those files.

Static inspection of the supplied artifacts found:

| Supplied file | Observed contract or status |
| --- | --- |
| `final_stm32.onnx`, `final_student_stm32_clean.onnx` | Opset 11; input `(1, 30, 23)`; output `(1, 25)`; no external-data references. |
| `final_student_stm32.onnx` | Earlier opset-18 graph with input `(1, 10, 20)`; requires its `final_student_stm32.onnx.data` file. |
| `final_stm32.onnx.data` | Present, but not referenced by the supplied `final_stm32.onnx` graph. |
| `satellite_real_data.npz`, `satellite_real_data_30.npz` | `input` arrays with FP32 shape `(100, 30, 23)`. Shape agreement does not prove association with particular model weights. |
| `satellite_real_input_only.npz` | FP32 input shape `(100, 20, 30)`; incompatible with the current model input. |
| `satellite_real_metadata.json` | Describes 30 features and shape `(100, 30, 30)`; does not describe the current 23-feature input. |
| `satellite_real_labels.npy` | 100 integer labels; association with the current exported inputs has not been established. |

For a new deployment attempt, generate the model, scaler, and validation inputs together in the same run directory. Check their feature order and dimensions before integration.

ONNX format validation does not run inference or establish numerical equivalence. The current notebook does not include the manuscript's 100-sample OpenCV–PyTorch comparison, ONNX test-set evaluation, STM32 firmware integration, or board timing and memory measurements. Those require separate execution and records. The folder contains no complete STM32 firmware project or board measurement logs.

## Dataset generation scripts

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
