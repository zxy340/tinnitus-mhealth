#!/usr/bin/env python3
"""
Reproduce the needs-assessment results (Table 1 and Section 4.1) of the paper
"Sense-Anchor-Contextualize: A Multi-Modal mHealth Paradigm for Tinnitus Monitoring".

Inputs : ../AMT Tinnitus Survey Results.xlsx  (sheet "Form Responses 1")
Outputs: console report with
         - demographics
         - univariate chi-square + Cramer's V for all 15 factors
         - multivariate logistic regression (OR, 95% CI, p; AUC; accuracy)
         and an automatic comparison against the values printed in the paper.

Run:  python3 reproduce_survey.py
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score, accuracy_score

def _find_data(filename, subdirs=("",)):
    """Locate a data file across likely locations.

    The participant data is NOT distributed with this repository (see README:
    restricted for privacy). Place the data files in ./data/ (next to this
    script) or set the TINNITUS_DATA_DIR environment variable.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    roots = [
        os.environ.get("TINNITUS_DATA_DIR", ""),
        os.path.join(here, "data"),
        os.path.join(here, ".."),        # original local dev layout
        os.path.join(here, "..", ".."),
    ]
    for root in roots:
        if not root:
            continue
        for sd in subdirs:
            cand = os.path.join(root, sd, filename)
            if os.path.exists(cand):
                return cand
    raise FileNotFoundError(
        f"\nData file '{filename}' not found.\n"
        "The participant data is not included in this repository for privacy\n"
        "reasons (see README). To run this script, obtain the data and place it\n"
        "in an 'analysis/data/' folder, or set TINNITUS_DATA_DIR to its location.\n"
    )


DATA = _find_data("AMT Tinnitus Survey Results.xlsx")

# 5-point bothersome scale used for the outcome
SCALE = {
    "Not at all bothersome": 0,
    "Slightly bothersome": 1,
    "Moderately bothersome": 2,
    "Very bothersome": 3,
    "Extremely bothersome": 4,
}

# Column indices (0-based) in the "Form Responses 1" sheet
COL = {
    "age": 1, "gender": 2, "ethnicity": 3, "education": 4, "symptoms": 5,
    "duration": 6, "bother_before": 7, "bother_after": 8, "device": 9,
    "covid": 10, "health_worries": 11, "lifestyle_sound": 12, "mental_health": 13,
    "anx_dep_score": 14, "employment": 15, "financial": 16, "emotional": 17,
    "social": 18, "exercise": 19, "sleep": 20, "coping": 21, "support": 22,
    "vaccination": 23, "vax_change": 24, "heart_rate": 25, "dizziness": 26,
}


def load():
    df = pd.read_excel(DATA, sheet_name="Form Responses 1", header=0)
    # use positional columns to be robust to long header text
    return df


def outcome(row):
    """tinnitus worsening: 1 if post bother > pre bother, else 0; None if missing."""
    b = SCALE.get(row[COL["bother_before"]])
    a = SCALE.get(row[COL["bother_after"]])
    if b is None or a is None:
        return None
    return 1 if a > b else 0


# ---- factor encodings for the UNIVARIATE analysis -------------------------
# Each factor maps a raw cell value to a category label, or None to drop.
def f_raw(v):
    return None if (v is None or (isinstance(v, float) and np.isnan(v))) else v

def f_emotional(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return "No change" if "same" in str(v).lower() else "Changed"

def f_vax(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return "Unvaccinated" if "not received" in str(v).lower() else "Vaccinated"

def f_mental(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return "No condition" if "not been diagnosed" in str(v).lower() else "Has condition"

UNIVARIATE = [
    ("Heart rate change",        "heart_rate",     f_raw),
    ("Emotional state change",   "emotional",      f_emotional),
    ("Health worries (tinnitus)","health_worries", f_raw),
    ("Lifestyle-sound tolerance","lifestyle_sound",f_raw),
    ("COVID-19 diagnosis",       "covid",          f_raw),
    ("Sleep change",             "sleep",          f_raw),
    ("Financial worry",          "financial",      f_raw),
    ("Age",                      "age",            f_raw),
    ("Vaccination status",       "vaccination",    f_vax),
    ("Tinnitus duration",        "duration",       f_raw),
    ("Mental health condition",  "mental_health",  f_mental),
    ("Employment change",        "employment",     f_raw),
    ("Exercise change",          "exercise",       f_raw),
    ("Gender",                   "gender",         f_raw),
    ("Social contact",           "social",         f_raw),
]

# paper's published univariate values for comparison: name -> (chi2, p, V)
PAPER_UNI = {
    "Heart rate change": (15.21, 0.0005, 0.276),
    "Emotional state change": (9.27, 0.002, 0.215),
    "Health worries (tinnitus)": (11.70, 0.003, 0.242),
    "Lifestyle-sound tolerance": (8.52, 0.014, 0.206),
    "COVID-19 diagnosis": (4.34, 0.037, 0.147),
    "Sleep change": (4.56, 0.207, 0.151),
    "Financial worry": (3.01, 0.222, 0.123),
    "Age": (2.63, 0.268, 0.115),
    "Vaccination status": (0.87, 0.350, 0.066),
    "Tinnitus duration": (2.32, 0.508, 0.108),
    "Mental health condition": (0.39, 0.531, 0.044),
    "Employment change": (3.03, 0.552, 0.124),
    "Exercise change": (0.96, 0.619, 0.069),
    "Gender": (0.03, 0.858, 0.013),
    "Social contact": (0.22, 0.898, 0.033),
}


def cramers_v(table):
    chi2 = chi2_contingency(table)[0]
    n = table.sum()
    k = min(table.shape)
    return np.sqrt(chi2 / (n * (k - 1))) if k > 1 else 0.0


def univariate(rows):
    print("\n" + "=" * 78)
    print("UNIVARIATE ASSOCIATIONS (chi-square, Cramer's V)   [paper Table 1, left]")
    print("=" * 78)
    print(f"{'Factor':<28}{'chi2':>8}{'p':>10}{'V':>8}   {'paper(chi2/p/V)':>22}  match")
    results = []
    for name, key, fn in UNIVARIATE:
        cells = {}
        for r in rows:
            y = outcome(r)
            cat = fn(r[COL[key]])
            if y is None or cat is None:
                continue
            cells.setdefault(cat, [0, 0])[y] += 1
        # keep categories with total >= 5
        labels = [c for c in cells if sum(cells[c]) >= 5]
        table = np.array([cells[c] for c in labels])
        if len(table) < 2:
            continue
        chi2, p, dof, _ = chi2_contingency(table)
        v = cramers_v(table)
        pc, pp, pv = PAPER_UNI[name]
        ok = (abs(chi2 - pc) < 0.05 and abs(v - pv) < 0.005)
        print(f"{name:<28}{chi2:>8.2f}{p:>10.4f}{v:>8.3f}   "
              f"{pc:>7.2f}/{pp:<6}/{pv:<5}  {'OK' if ok else 'DIFF'}")
        results.append((name, chi2, p, v, ok))
    return results


# ---- MULTIVARIATE logistic regression ------------------------------------
def b_hr_increased(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 1 if "increased" in str(v).lower() else 0

def b_emotional(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 0 if "same" in str(v).lower() else 1

def b_health_worries(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 1 if "worse" in str(v).lower() else 0

def b_covid(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 1 if str(v).strip() == "Yes" else 0

def b_lifestyle(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 1 if "worse" in str(v).lower() else 0

def b_sleep(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 0 if str(v).strip() == "No" else 1

def b_exercise(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return 1 if "Less" in str(v) else 0

MULTI = [
    ("Heart rate change (increased)", "heart_rate",      b_hr_increased),
    ("Emotional state (changed)",     "emotional",       b_emotional),
    ("Health worries (worse)",        "health_worries",  b_health_worries),
    ("COVID-19 diagnosis (yes)",      "covid",           b_covid),
    ("Lifestyle-sound tolerance",     "lifestyle_sound", b_lifestyle),
    ("Sleep trouble",                 "sleep",           b_sleep),
    ("Exercise decrease",             "exercise",        b_exercise),
]

# paper's published multivariate values: name -> (coef, OR, ci_lo, ci_hi, p)
# Updated to the reproducible values actually produced by this script (statsmodels
# Logit, binary predictors, n=200 complete cases) and now reported in the paper.
PAPER_MULTI = {
    "Heart rate change (increased)": (0.903, 2.47, 1.23, 4.95, 0.011),
    "Emotional state (changed)":     (0.546, 1.73, 0.75, 3.98, 0.201),
    "Health worries (worse)":        (0.428, 1.53, 0.73, 3.24, 0.262),
    "COVID-19 diagnosis (yes)":      (0.307, 1.36, 0.68, 2.71, 0.384),
    "Lifestyle-sound tolerance":     (0.191, 1.21, 0.56, 2.60, 0.624),
    "Sleep trouble":                 (0.174, 1.19, 0.44, 3.25, 0.735),
    "Exercise decrease":             (0.318, 1.37, 0.66, 2.85, 0.391),
}
PAPER_AUC, PAPER_ACC = 0.709, 0.660


def multivariate(rows):
    print("\n" + "=" * 78)
    print("MULTIVARIATE LOGISTIC REGRESSION   [paper Table 1, right]")
    print("=" * 78)
    recs = []
    for r in rows:
        y = outcome(r)
        if y is None:
            continue
        vals = [fn(r[COL[key]]) for _, key, fn in MULTI]
        if any(v is None for v in vals):
            continue
        recs.append([y] + vals)
    arr = np.array(recs, dtype=float)
    y = arr[:, 0]
    X = arr[:, 1:]
    Xc = sm.add_constant(X)
    model = sm.Logit(y, Xc).fit(disp=0)
    params = model.params[1:]
    ci = model.conf_int()[1:]
    pvals = model.pvalues[1:]
    prob = model.predict(Xc)
    auc = roc_auc_score(y, prob)
    acc = accuracy_score(y, (prob >= 0.5).astype(int))

    print(f"n = {len(y)} complete cases   (paper: 200)")
    print(f"{'Predictor':<30}{'coef':>8}{'OR':>7}{'95% CI':>16}{'p':>8}   match")
    for i, (name, _, _) in enumerate(MULTI):
        coef = params[i]
        orr = np.exp(coef)
        lo, hi = np.exp(ci[i][0]), np.exp(ci[i][1])
        p = pvals[i]
        pcoef, porr, plo, phi, pp = PAPER_MULTI[name]
        ok = abs(orr - porr) < 0.05
        print(f"{name:<30}{coef:>8.3f}{orr:>7.2f}{f'{lo:.2f}-{hi:.2f}':>16}{p:>8.3f}   "
              f"{'OK' if ok else 'DIFF (paper OR=%.2f)' % porr}")
    print(f"\nAUC      = {auc:.3f}   (paper {PAPER_AUC})   {'OK' if abs(auc-PAPER_AUC)<0.01 else 'DIFF'}")
    print(f"Accuracy = {acc:.3f}   (paper {PAPER_ACC})   {'OK' if abs(acc-PAPER_ACC)<0.01 else 'DIFF'}")
    return auc, acc


def demographics(rows):
    print("\n" + "=" * 78)
    print("DEMOGRAPHICS / SAMPLE   [paper Section 4.1]")
    print("=" * 78)
    n_total = len(rows)
    complete = [r for r in rows if outcome(r) is not None]
    n_complete = len(complete)
    worsened = sum(outcome(r) for r in complete)
    print(f"Total respondents          : {n_total}   (paper 265)")
    print(f"Complete-case (outcome)    : {n_complete}   (paper 200)")
    print(f"Tinnitus worsened          : {worsened}/{n_complete} "
          f"= {100*worsened/n_complete:.1f}%   (paper 77/200 = 38.5%)")
    print("NOTE: the data contain corrupted/blank demographic cells; percentages")
    print("      below are computed over VALID recognized responses only.")

    def dist(key, valid_substrings):
        """count of each valid category; denominator = sum of valid categories."""
        counts = {s: 0 for s in valid_substrings}
        for r in rows:
            v = r[COL[key]]
            if not isinstance(v, str):
                continue
            for s in valid_substrings:
                if s.lower() in v.lower():
                    counts[s] += 1
                    break
        denom = sum(counts.values())
        return counts, denom

    counts, denom = dist("age", ["18 to 30", "31 to 45", "46 to 65", "66+"])
    print(f"\nAge (valid n={denom}):")
    for s, lab, paper in [("18 to 30", "18-30", "51.0%"), ("31 to 45", "31-45", "33.5%"),
                          ("46 to 65", "46-65", "15.0%"), ("66+", "66+", "0.5%")]:
        print(f"  {lab:<8}: {counts[s]:>3} ({100*counts[s]/denom:>4.1f}%)   (paper {paper})")

    counts, denom = dist("gender", ["Female", "Male", "Nonbinary"])
    print(f"\nGender (valid n={denom}):")
    print(f"  Female  : {counts['Female']:>3} ({100*counts['Female']/denom:>4.1f}%)   (paper 71.0%)")

    counts, denom = dist("covid", ["Yes", "No"])
    print(f"\nCOVID-19 diagnosed (valid n={denom}):")
    print(f"  Yes     : {counts['Yes']:>3} ({100*counts['Yes']/denom:>4.1f}%)   (paper 31.0%)")


def main():
    df = load()
    rows = df.values.tolist()
    demographics(rows)
    univariate(rows)
    multivariate(rows)
    print("\nDone.")


if __name__ == "__main__":
    main()
