# Tinnitus Multi-Modal mHealth Monitoring App

A patient-facing Flutter application for multi-modal tinnitus monitoring that integrates
**objective wearable physiological data** (heart rate, sleep, activity) with **subjective
symptom self-reports**, following the **Sense-Anchor-Contextualize (SAC)** design paradigm
for episodic chronic disease monitoring.

This repository accompanies the paper:

> *Sense-Anchor-Contextualize: A Multi-Modal mHealth Paradigm for Tinnitus Monitoring.*
> Xiaoyu Zhang, Wei Bo, Liyao Li, Longxiang Pan, Huining Li, Wei Sun, Wenyao Xu.
> University at Buffalo, SUNY.

## What it does

The app implements the three data-collection modules of the SAC paradigm:

| Module (in `lib/`)        | SAC role               | Collection           | Description                                                            |
|---------------------------|------------------------|----------------------|-----------------------------------------------------------------------|
| `pages/calendar/`         | **Anchor**             | Active, event-driven | Tinnitus Event Calendar — patient logs an episode (severity + emotion) |
| `pages/poll/`             | **Sense (subjective)** | Active, daily        | Daily Feelings survey (stress, mood, fatigue, sleep, activity, social) |
| `pages/smartwatch/`       | **Sense (passive)**    | Passive, continuous  | Behaviorome — heart rate, sleep, steps, activity from the wearable     |
| `FirestoreService.dart`   | **Contextualize**      | —                    | Unified timestamped writes to Firebase Firestore for event-anchored retrieval |

## Architecture

- **Frontend:** Flutter (Dart), Android (iOS scaffolding included)
- **Backend:** Firebase (Authentication + Cloud Firestore)
- **Wearable:** physiological data ingested via the platform health APIs / Bluetooth Low Energy

## Setup

This repository does **not** include Firebase credentials. To build and run:

1. Install [Flutter](https://flutter.dev/docs/get-started/install).
2. Create your own Firebase project and an Android app with package name `buffalo.reu.tinnitus_app`.
3. Download your `google-services.json` and place it at `android/app/google-services.json`
   (a template is provided at `android/app/google-services.json.example`).
4. Enable **Email/Password Authentication** and **Cloud Firestore** in the Firebase console,
   and configure Firestore Security Rules appropriately.
5. Fetch dependencies and run:
   ```bash
   flutter pub get
   flutter run
   ```

> **Note on data privacy.** No participant data is included in this repository. Per the
> accompanying study, pilot deployment data are not publicly released due to the small
> sample size and re-identification risk.

## Repository structure

```
lib/
  main.dart                 app entry point
  FirestoreService.dart     unified timestamped data layer (Contextualize)
  pages/
    home.dart               navigation shell
    profile.dart            authentication / profile
    calendar/               Tinnitus Event Calendar (Anchor)
    poll/                    Daily Feelings survey (Sense, subjective)
    smartwatch/             Behaviorome wearable data (Sense, passive)
      parts/                heart, sleep, step, activity views
android/, ios/              platform projects
fonts/                      bundled fonts
```

## Citation

If you use this software, please cite the accompanying paper (full reference and venue to be
added upon publication).

## License

Released under the MIT License — see [LICENSE](LICENSE).
