# Contributing

## Scope and language

- Keep all new documentation, notebook markdown, comments, and status text in English.
- Keep claims factual and tied to available evidence.

## Notebook preservation rules

- Preserve `model/model.ipynb` byte-for-byte once it is supplied.
- Do not rerun, clear outputs, reorder cells, or alter execution history in the preserved original.
- Use a separate working copy for new runs.

## Experiment structure

- Keep preprocessing, training, evaluation, visualization, and export in notebook-centered workflows.
- Do not replace the notebook experiment with a separate train/evaluate/export pipeline.

## Output management

- Write new run artifacts to unique directories under `runs/<run_id>/`.
- Do not overwrite historical notebook outputs, supplied scaler files, or embedded artifacts.

## Validation and reporting

- Run lightweight repository checks before submitting updates.
- Mark unavailable-data checks as skipped with a reason.
- Distinguish historical results from newly executed results.
