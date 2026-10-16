# AI4薄肌

## Use as a Codex project

1. Open the repository directory in Codex.
2. Start a new conversation by asking `$ai4boji` to read your profile. It uses repository-local `data/`, unless you specify the same absolute `--data-dir` each time.
3. Report today’s state or actual activity. Only reported details should be recorded.
4. Codex calls the CLI and verifies the saved result. Refresh the dashboard to see the same data.

Full field definitions: [protocol.md](../../.agents/skills/ai4boji/references/protocol.md). Do not put personal records in public issues.

## Common commands

Run from the repository root:

```bash
python3 -m ai4boji --lang en context
python3 -m ai4boji --lang en plan
python3 -m ai4boji --lang en report --days 14 --format markdown
python3 -m ai4boji history plan:2026-10-16
```

Save a user-confirmed preference:

```bash
python3 -m ai4boji memory <<'JSON'
{"id":"memory:weekend-time","text":"I prefer morning training on weekends","kind":"preference","confirmed":true}
JSON
```

Corrections reuse the ID and include the `expected_revision` you read. `python3 -m ai4boji forget memory:weekend-time` permanently removes the memory and its revisions.

## Edits and retries

`profile` merges partial updates. `checkin`, `log` and `memory` replace their entire payload. Read the current entry and merge a correction before submitting. The dashboard checks revisions; reload after conflicts rather than forcing stale data over another update.

Reuse one ID for the same real training session. Identical content with the same ID preserves its version; corrections increase the version. Only genuinely separate sessions get separate IDs. After saving, the dashboard remains in edit mode for that record. Choose Cancel to start another record.

## Planning scope

Starter plans use structured time, equipment, weekdays and recovery feedback. Codex interprets free-text goals, food context and preferences; local templates do not. Pain or restrictions pause strength planning. Past pain remains unresolved until an explicit pain-free check-in on a later date. Correct erroneous records directly instead of bypassing them by removing profile text.

The top date picker selects historical views without mutating plans. A changed profile may mark an old plan stale. The CLI exposes earlier plan revisions.

## Data and troubleshooting

- Occupied port: use `--port 18765` and open the newly printed URL.
- Moving projects: move the private `data/` directory too, or keep using an absolute `--data-dir`.
- Resetting a demo: stop its server and move `.demo/` aside before restarting. Keep personal `data/` separate.
- Saving fails: ensure the server is running and open its printed loopback URL; reload before retrying. Do not open the HTML file directly.
- Missing timezone data: use Python with an IANA database. Windows installations without it can install `tzdata`; normal macOS/Linux environments need no additional package.
- Backup: stop the server and copy the private data directory. Memory deletion does not remove external backups or existing Codex conversations.
- This server is for one local user. It has no multi-account system, cloud synchronization or public production hosting setup.
