# AI4薄肌 command protocol

Run from repository root. Put `--data-dir /absolute/private/path` and `--lang en` before the subcommand when needed. Read data with `context` or `state` first. Use UTF-8 JSON files under ignored `work/` or stdin; never put user free text inside shell interpolation. Commands return JSON and use exit code 2 on validation errors.

## Profile

`python3 -m ai4boji profile --input work/profile.json`

Required for first creation: `name` (text), `age` (integer 18–100), `goal` (text), `minutes` (integer 10–90), `days` (1–3 unique integers, Monday=0), `equipment` (`bodyweight` or `dumbbells`). Optional: `restrictions`, `diet`, `timezone` (IANA; default Asia/Shanghai), `locale` (zh-CN/en), `expected_revision`.

Later profile writes merge the provided fields. Use empty text to clear a restriction only when the user actually reports it no longer applies. The goal, diet and memory texts are context for Codex, not automatic constraints parsed by the rule engine.

## Check-in

`python3 -m ai4boji checkin --input work/checkin.json`

Fields: `date` (YYYY-MM-DD, defaults to profile-local today), optional `sleep_hours` (0–24), `energy` (integer 1–5), `soreness` (integer 0–5), `minutes` (integer 5–90), `pain` (boolean), `note` (text), `expected_revision`.

ID is `checkin:DATE`. This replaces the payload, so merge only confirmed updates into the last saved check-in. Omit unreported numeric fields rather than entering zero. `pain: false` is an explicit user report, not a default. A later pain-free check-in clears prior pain; a same-day pain record remains conservative until clarified on a subsequent day or corrected by the user.

## Plan

`python3 -m ai4boji plan --date YYYY-MM-DD`

Returns a persisted plan with `mode`, `exercises`, `reasons`, source IDs, rule version and fingerprint. Identical evidence returns the same revision. Updated evidence produces a new revision. `context` reports `plan.stale` if data changed since generation. Plans can be drafted for future dates; actual records cannot be future-dated. Re-reading a historical date is read-only until `plan` is explicitly called.

## Activity log

`python3 -m ai4boji log --input work/log.json`

Required: `id` (stable ASCII session ID), `status` (`completed`, `partial`, `rest`, `skipped`). Optional: `date`, `duration_min` (integer 0–300), `weight_kg` (20–400), `waist_cm` (30–300), `effort` (1–10), `pain` (boolean), `note`, `exercises`, `expected_revision`.

Example ID: `log:2026-10-16-session-1`. Reuse it on retries. For editing, preserve the ID and pass the revision read earlier. This replaces the payload, so merge user corrections into the full existing payload first. Rest/skipped may record easy activity minutes but cannot include strength sets; report totals count completed/partial training only.

`exercises` entries: `exercise_id`, `sets`, `reps`, `load_kg`. IDs in v0.1: `chair-squat`, `wall-pushup`, `hip-hinge`, `bird-dog`, `db-row`. Sets 1–20, reps 1–100, load 0–300 kg. Each row groups sets with the same reps and load; split differing sets into rows. Load is per dumbbell, or 0 for unloaded movement. Unknown exercises can be described in notes, without fabricating a catalog ID.

## Memory

`python3 -m ai4boji memory --input work/memory.json`

Fields: `id` (optional `memory:slug`, use stable IDs for corrections), `text`, `kind` (`fact`, `preference`, `inference`), `confirmed` (boolean, default false), `expires` (optional YYYY-MM-DD), `expected_revision`.

Inferences cannot be confirmed. `fact` and `preference` sources are user; `inference` source is Codex. Expiry is inclusive in the profile-local calendar. `forget memory:slug` permanently removes that memory and its revisions. It leaves unrelated records intact.

## Read, report, export

- `context [--date DATE]`: profile, selected plan/check-in, 14-day actual records, active memories and summary; suitable for a new Codex conversation.
- `state [--date DATE]`: full bilingual current data and exercise catalog for inspection.
- `history ID`: previous versions; current value is returned by state/context.
- `report --days 7 [--date DATE] [--format markdown]`: actual recorded training, calendar gaps, measurements and source IDs.
- `export`: current entries as language-neutral JSON. No import command or revision archive is included. For backup, stop the service and copy the data directory.

Browser and CLI access the same database. Avoid editing the SQLite file directly. The runtime JSON validation in `core.py` is authoritative; `schemas/records.json` documents the API shapes.
