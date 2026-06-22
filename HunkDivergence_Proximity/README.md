# Hunk Divergence & Spatial Proximity — Results Interpretation 

Every definition, formula, and code below is taken from the source paper:

*Characterizing Multi-Hunk Patches: Divergence, Proximity, and LLM Repair Challenges* — Nashid, Ding, Gallaba, Hassan, Mesbah (https://arxiv.org/abs/2506.04418)

---

## 1. What Is a Multi-Hunk Patch?

**Hunk:** A hunk is a block of consecutive edits applied to a specific region of source code. Each hunk $h_i$ is represented as a tuple of its location (line range), modified token sequence (content), file path, enclosing method identifier, and package path.

**Multi-Hunk Patch:** A multi-hunk patch $P$ is a set of $n \ge 2$ distinct hunks, $P = \{h_1, h_2, ..., h_n\}$, where the hunks modify **non-contiguous** regions of source code. $P$ is an atomic change intended to address a single bug.

---

## 2. Hunk Divergence

Hunk divergence measures the internal heterogeneity of a multi-hunk patch by calculating the lexical, structural, and file-level distances between all pairs of hunks in the patch.

### 2.1 Pairwise Hunk Divergence

The pairwise divergence between two hunks $h_1$ and $h_2$ is defined as:

$$Div(h_1, h_2) = \frac{D_{lex} \cdot (D_{ast} + \gamma \cdot D_{file})}{1 + \gamma}$$

Where:
- **$D_{lex}(h_i, h_j)$ (Lexical Distance):** Computed as $1 - \text{BLEU}(T_i, T_j)$, where $T_i$ and $T_j$ are the token sequences of the two hunks.
- **$D_{ast}(h_i, h_j)$ (Structural/AST Distance):** Measures the structural distance between AST nodes of the two hunks normalized by the tree diameter. If the two hunks are in different files, structural comparison is undefined, and $D_{ast}$ is set to $1$.
- **$D_{file}(h_i, h_j)$ (File-Level Distance):** Measures the folder-level separation. It is $0$ if both hunks are in the same file; otherwise, it is based on the longest common prefix (LCP) of the directory paths.
- **$\gamma$ (Scaling Factor):** Amplifies the influence of file-level separation. $\gamma = 1.0$ for hunk pairs in the same file, and $\gamma = 2.0$ for hunk pairs in different files.

### 2.2 Patch-Level Hunk Divergence

The overall divergence of a patch $P$ with $n$ hunks is defined as:

$$Div(P) = \ln(n) \cdot \left[ \frac{2}{n(n-1)} \cdot \sum_{1 \le i < j \le n} Div(h_i, h_j) \right]$$

The bracketed term represents the average pairwise divergence over all hunk pairs, while $\ln(n)$ scales the divergence to reflect the coordination complexity of having more hunks. For single-hunk patches ($n < 2$), hunk divergence is undefined (or set to $0.0$).

### 2.3 Results for our Dataset

The following table presents the median and mean values of the hunk divergence components computed over the 15 multi-hunk bugs in our dataset (from [`bugwise_average_divergence.csv`](https://github.com/NGimhana/PR-metrics/blob/main/HunkDivergence_Proximity/hunk_divergence/bugwise_average_divergence.csv)):

| Component | Median | Mean |
|---|---|---|
| Lexical ($D_{lex}$) | 0.9032 | 0.7854 |
| Structural ($D_{ast}$) | 0.5349 | 0.5043 |
| File ($D_{file}$) | 0.0000 | 0.0000 |
| **Overall $Div(P)$** | **0.3362** | **0.3326** |

**Key Observations:**
- **Overall Hunk Divergence** ranges from a minimum of **0.0000** to a maximum of **0.7423**, with a median of **0.3362** and a mean of **0.3326**.
* A higher number mean greater internal heterogeneity (dissimilarity) among the changes within a patch. --> repair is difficult
- **File Distance ($D_{file}$)** is **0.0000** for all bugs because all multi-hunk bugs in our dataset belong to the same file (`Cluster` class).

---

## 3. Spatial Proximity

Spatial proximity categorizes patches based on how spread out their hunks are across methods, files, and packages.

### 3.1 Predicates

- **$SM(P)$ (Same Method):** All hunks are in the same method.
- **$SF(P)$ (Same File):** All hunks are in the same file.
- **$SP(P)$ (Same Package):** All hunks are in the same package.
- **$LCP(P)$ (Longest Common Prefix):** The minimum directory depth shared across all hunk pairs.

### 3.2 The Five Proximity Classes

Based on these predicates, patches are classified into one of five categories:

| Class | Condition | Description |
|---|---|---|
| **Nucleus** | $SF(P) \land SM(P)$ | All hunks are confined to a single method in the same file. |
| **Cluster** | $SF(P) \land \neg SM(P)$ | Hunks are in the same file but span different methods. |
| **Orbit** | $\neg SF(P) \land SP(P)$ | Hunks span multiple files within the same package. |
| **Sprawl** | $\neg SF(P) \land \neg SP(P) \land LCP(P) > \lambda$ | Hunks are in different packages but share some directory hierarchy. |
| **Fragment** | $\neg SF(P) \land \neg SP(P) \land LCP(P) \le \lambda$ | Hunks are widely scattered across unrelated packages. |

$\lambda$ is the directory depth threshold, set to $3$ in our analysis.

### 3.3 Resultsf for Our Dataset

The distribution of spatial proximity classes and their average hunk divergence in our dataset (derived from [`proximity_class.csv`](https://github.com/NGimhana/PR-metrics/blob/main/HunkDivergence_Proximity/proximity_class/proximity_class.csv) and [`proximity_class_avg_hunk_divergence.csv`](https://github.com/NGimhana/PR-metrics/blob/main/HunkDivergence_Proximity/proximity_class/proximity_class_avg_hunk_divergence.csv)):

| Proximity Class | Number of Bugs | Mean Hunk Divergence |
|---|---|---|
| **Nucleus** | 82 | N/A |
| **Cluster** | 15 | 0.3326 |
| **Orbit** | 0 | N/A |
| **Sprawl** | 0 | N/A |
| **Fragment** | 0 | N/A |
| **Total** | **97** | **0.3326** (average over multi-hunk bugs) |

**Key Observations:**

- A higher value means The hunks are more spread out across the architecture of the codebase.
- **Nucleus** contains **82 bugs**. These are single-hunk patches where all changes are confined to a single method in a single file. Because they only contain one hunk, hunk divergence is not computed for them.
- **Cluster** contains **15 bugs**. These are multi-hunk patches where hunks span multiple methods but are restricted to a single file. Their average hunk divergence is **0.3326**.
- There are **no bugs** classified as **Orbit**, **Sprawl**, or **Fragment** in our current dataset, reflecting that all analysed bugs in this dataset are single-file modifications.

---

## 4. Our Dataset

The dataset evaluated in this workspace consists of 97 bugs across various open-source Android projects:

- **Total Bugs:** 97
- **Hunk Count Distribution:**
  - **1 Hunk:** 82 bugs (84.5%) — classified as `Nucleus`.
  - **2 Hunks:** 8 bugs (8.2%) — classified as `Cluster`.
  - **3 Hunks:** 7 bugs (7.2%) — classified as `Cluster`.
- **Project Breakdown:**
  - `bug`: 49 bugs
  - `realbug`: 18 bugs
  - `pslab`: 7 bugs
  - `harmonic`: 6 bugs
  - `urlcheck`: 5 bugs
  - `Anki` (AnkiDroid): 3 bugs
  - `WiFiAnalyzer`: 3 bugs
  - `gpslogger`: 2 bugs
  - `markor`: 2 bugs
  - `skytube`: 1 bug
  - `ultrasonic`: 1 bug

