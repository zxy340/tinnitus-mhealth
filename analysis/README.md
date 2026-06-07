# Reproduction code

Analysis scripts that regenerate the quantitative results reported in the paper
*Sense-Anchor-Contextualize: A Multi-Modal mHealth Paradigm for Tinnitus Monitoring*
directly from the raw study data.

## ⚠️ Data is not included in this repository

The participant data are **restricted** and are **not distributed here** for privacy /
re-identification reasons (consistent with the manuscript's data-availability statement).
The scripts therefore will not run on a fresh clone until the data are supplied.

Two files are required:

| Required file                       | Used by               |
|-------------------------------------|-----------------------|
| `AMT Tinnitus Survey Results.xlsx`  | `reproduce_survey.py` |
| `output-1_edit.json`                | `reproduce_pilot.py`  |

To run, obtain the data (available from the corresponding author upon reasonable request)
and place the files in an `analysis/data/` folder:

```
analysis/
  data/
    AMT Tinnitus Survey Results.xlsx
    output-1_edit.json
```

Alternatively, set `TINNITUS_DATA_DIR` to the directory that contains the files.

## Files

| File                  | Reproduces                                                           |
|-----------------------|---------------------------------------------------------------------|
| `reproduce_survey.py` | Section 4.1 / Table 1 — demographics, univariate chi-square + Cramer's V, multivariate logistic regression |
| `reproduce_pilot.py`  | Section 4.3 — per-user coverage, multi-modal overlap days, compliance, the 07-12 event snapshot |
| `requirements.txt`    | Python dependencies                                                  |

## Environment & run

```bash
pip install -r requirements.txt
python3 reproduce_survey.py
python3 reproduce_pilot.py
```

Each script prints its computed values alongside the values reported in the paper and
flags any mismatch (`OK` / `DIFF`). With the correct data in place, all checks pass.

## What is reproduced

- **Demographics** (Section 4.1): age, gender, and COVID-19 distributions over valid
  responses; outcome prevalence (tinnitus worsened = 77/200 = 38.5%).
- **Univariate analysis** (Table 1, left): chi-square and Cramer's V for all 15 candidate
  factors. Heart rate change is the strongest factor (chi2 = 15.21, p = 0.0005, V = 0.276).
- **Multivariate logistic regression** (Table 1, right): odds ratios with 95% confidence
  intervals, AUC, and accuracy. Heart rate change is the only significant independent
  predictor (OR = 2.47, 95% CI 1.23–4.95, p = 0.011; model AUC = 0.709, n = 200).
- **Pilot** (Section 4.3): per-user heart-rate / sleep / activity coverage, the five
  multi-modal overlap days for User 3, Daily-Feelings compliance (7/33 = 21%), and the
  07-12 event snapshot.

## Notes

- Demographic percentages are computed over *valid* responses; a number of rows contain
  blank or corrupted demographic cells and are excluded from those denominators (they are
  retained wherever their other fields are valid).
- The figures reported in the manuscript correspond to the output of these scripts; this
  repository is the authoritative source for the reported numbers.
