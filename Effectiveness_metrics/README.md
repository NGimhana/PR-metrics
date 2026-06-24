## Results

All the results CSVs for each of the metrics are available in the `Effectiveness_metrics/agent-logs` directory. The results are organized by the metric name and the corresponding setting (e.g., `codex`, `gemini`, and `claude`).

## Metric Definitions

Based on the paper, the three effectiveness metrics are defined as follows:

- Localization: file-level success at identifying all ground-truth buggy files. A localization score of 1 means the agent modified every buggy file in the developer patch, even if it also touched extra files; otherwise it is 0.
- Compilation: whether the generated patch is non-empty and compiles without errors. A compilation score of 1 means the patch is syntactically coherent across all changed regions; otherwise it is 0. Search for BUILD SUCCESSFUL in the logs.
- Repair: whether the generated patch is non-empty and passes all available tests. A repair score of 1 means the patch restores correctness with no remaining test failures; otherwise it is 0.