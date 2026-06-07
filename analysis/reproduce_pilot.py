#!/usr/bin/env python3
"""
Reproduce the proof-of-concept pilot results (Section 4.3 and Listing 1) of the paper
"Sense-Anchor-Contextualize: A Multi-Modal mHealth Paradigm for Tinnitus Monitoring".

Input : ../tinnitus_export/output-1_edit.json   (Firestore export, 3 test users)
Output: console report with
        - per-user data coverage (heart rate / sleep / activity days, compliance)
        - User 3 multi-modal overlap days
        - User 3 event snapshot for 2022-07-12, compared against the paper's Listing 1
          (this surfaces several values in Listing 1 that DO NOT match the raw data).

Run:  python3 reproduce_pilot.py
"""

import os
import json

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


DATA = _find_data("output-1_edit.json", subdirs=("", "tinnitus_export"))

USERS = {
    "User 1": "tinnitustest1@gmail.com",
    "User 2": "tinnitustest2@gmail.com",
    "User 3": "tinnitustest3@gmail.com",
}

# paper Section 4.3 per-user numbers: name -> (total, hr, sleep, activity, DF, TE)
PAPER = {
    "User 1": (6, 3, 1, 6, 1, 1),
    "User 2": (43, 37, 31, 41, 3, 0),
    "User 3": (33, 25, 15, 32, 7, 8),
}


def load():
    with open(DATA) as f:
        return json.load(f)["users"]


def coverage(users):
    print("=" * 78)
    print("PER-USER DATA COVERAGE   [paper Section 4.3]")
    print("=" * 78)
    print(f"{'User':<8}{'total':>6}{'HR':>8}{'sleep':>9}{'activity':>10}{'DF':>5}{'TE':>5}   match")
    for name, email in USERS.items():
        u = users[email]
        beh = u.get("Behaviorome", {})
        total = len(beh)
        hr = sum(1 for d in beh.values() if "Heart" in d)
        sleep = sum(1 for d in beh.values() if "Sleep" in d)
        # "activity" coverage = days with any movement signal (Activity OR Step)
        activity = sum(1 for d in beh.values() if ("Activity" in d or "Step" in d))
        df = len(u.get("Daily Feelings", {}))
        te = len(u.get("Tinnitus Event Calendar", {}))
        got = (total, hr, sleep, activity, df, te)
        exp = PAPER[name]
        ok = got == exp
        pct = lambda a, b: f"{a}({round(100*a/b)}%)" if b else f"{a}"
        print(f"{name:<8}{total:>6}{pct(hr,total):>8}{pct(sleep,total):>9}"
              f"{pct(activity,total):>10}{df:>5}{te:>5}   "
              f"{'OK' if ok else 'DIFF exp=%s' % (exp,)}")


def overlap_and_compliance(users):
    print("\n" + "=" * 78)
    print("USER 3: MULTI-MODAL OVERLAP & COMPLIANCE   [paper Section 4.3]")
    print("=" * 78)
    u = users["tinnitustest3@gmail.com"]
    beh = u["Behaviorome"]
    hr_days = {d for d, v in beh.items() if "Heart" in v}
    sleep_days = {d for d, v in beh.items() if "Sleep" in v}
    te = u["Tinnitus Event Calendar"]
    event_dates = sorted({k.split(" ")[0] for k in te})  # date part of timestamp
    overlap = [d for d in event_dates if d in hr_days and d in sleep_days]
    print(f"Tinnitus events           : {len(te)}   (paper 8)")
    print(f"Unique event dates        : {len(event_dates)}")
    print(f"Event dates w/ HR + sleep : {len(overlap)}  -> {overlap}")
    print(f"  (paper: 'five overlap days' = 5)   {'OK' if len(overlap)==5 else 'DIFF'}")
    df = u.get("Daily Feelings", {})
    total_days = len(beh)
    comp = len(df) / total_days
    print(f"Daily Feelings compliance : {len(df)}/{total_days} = {100*comp:.0f}%   "
          f"(paper 21%)   {'OK' if round(100*comp)==21 else 'DIFF'}")


def _hm(s):
    """'4h 33m' -> minutes"""
    h, m = 0, 0
    for part in s.split():
        if part.endswith("h"):
            h = int(part[:-1])
        elif part.endswith("m"):
            m = int(part[:-1])
    return h * 60 + m


def snapshot_0712(users):
    print("\n" + "=" * 78)
    print("USER 3: EVENT SNAPSHOT 2022-07-12  vs  PAPER LISTING 1")
    print("=" * 78)
    u = users["tinnitustest3@gmail.com"]
    rec = u["Behaviorome"]["07-12-2022"]
    sleep = rec["Sleep"]["Features"]
    deep = _hm(sleep["Deep Sleep"]); light = _hm(sleep["Light Sleep"]); rem = _hm(sleep.get("REM Sleep", "0h 0m"))
    total_sleep = deep + light + rem
    heart = rec.get("Heart", {})
    hr_feat = heart.get("Features", {})
    hourly = heart.get("Hourly Heart Rate", {})
    steps = rec.get("Step", {}).get("Features", {}).get("Total Step Count")
    df = u["Daily Feelings"]["07-12-2022"]
    ev = u["Tinnitus Event Calendar"]["07-12-2022 11:30 PM"]

    # user's mean daily steps and mean avg-HR for baseline context
    beh = u["Behaviorome"]
    step_days = [v["Step"]["Features"]["Total Step Count"] for v in beh.values()
                 if "Step" in v and "Total Step Count" in v["Step"]["Features"]]
    mean_steps = sum(step_days) / len(step_days)
    hr_avgs = [v["Heart"]["Features"]["Average Heart Rate"] for v in beh.values()
               if "Heart" in v and "Average Heart Rate" in v["Heart"]["Features"]]
    mean_hr = sum(hr_avgs) / len(hr_avgs)

    print("RAW DATA (ground truth from the export):")
    print(f"  Tinnitus event 07-12 23:30 : {ev}")
    print(f"  Sleep                      : deep {deep}m + light {light}m + REM {rem}m = {total_sleep}m "
          f"({total_sleep//60}h{total_sleep%60}m)")
    print(f"  Heart (daily)              : min {hr_feat.get('Minimum Heart Rate')}, "
          f"max {hr_feat.get('Maximum Heart Rate')}, avg {hr_feat.get('Average Heart Rate')}")
    print(f"  Heart (hourly near event)  : 22:00={hourly.get('22:00')}, 23:00={hourly.get('23:00')} "
          f"(data is HOURLY; no 22:30/23:30 exist)")
    print(f"  Steps 07-12                : {steps}")
    print(f"  Daily Feelings (q1..q6)    : {[df.get('question %d'%i) for i in range(1,7)]}")
    print(f"  Baseline: mean daily steps = {mean_steps:.0f}, mean daily avg-HR = {mean_hr:.1f}")

    # Checks against the CORRECTED Listing 1 (only values that exist in the raw data).
    print("\nCORRECTED LISTING 1   vs   RAW DATA:")
    checks = [
        ("Event severity = 3",         str(ev.get("question 2")) == "3", f"raw question 2={ev.get('question 2')}"),
        ("Sleep total 4h33m",          total_sleep == 4*60+33, f"raw {total_sleep//60}h{total_sleep%60}m"),
        ("Deep sleep 0h45m",           deep == 45,             f"raw {deep}m"),
        ("HR 22:00 = 84 bpm",          hourly.get("22:00") == 84, f"raw 22:00={hourly.get('22:00')}"),
        ("HR 23:00 = 80 bpm",          hourly.get("23:00") == 80, f"raw 23:00={hourly.get('23:00')}"),
        ("Daily mean HR 77",           hr_feat.get("Average Heart Rate") == 77, f"raw avg={hr_feat.get('Average Heart Rate')}"),
        ("User mean HR ~75",           abs(mean_hr-75) < 1.0,  f"raw mean avg-HR {mean_hr:.1f}"),
        ("Daily stress 3/3",           df.get("question 1") == 3, f"raw q1={df.get('question 1')}"),
        ("Daily depression 2/3",       df.get("question 2") == 2, f"raw q2={df.get('question 2')}"),
    ]
    for claim, ok, detail in checks:
        print(f"  [{'MATCH' if ok else 'MISMATCH'}] {claim:<24} {detail}")
    print("\nNote: the original Listing 1 also claimed 'Activity 2,300 steps (~60% below")
    print("baseline)' and a sub-hourly HR trajectory (22:30/23:00/23:30); both are absent")
    print(f"from the data (raw steps on 07-12 = {steps}, above the {mean_steps:.0f}-step mean;")
    print("heart rate is recorded hourly). Those values were removed in the corrected Listing 1.")


def main():
    users = load()
    coverage(users)
    overlap_and_compliance(users)
    snapshot_0712(users)
    print("\nDone.")


if __name__ == "__main__":
    main()
