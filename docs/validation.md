# AI4薄肌

Local validation date: **2026-10-16**. All validation data is synthetic.

## Automated

- `python3 -m unittest discover -s tests -v`: 25 passing tests on Python 3.9.6.
- Official Skill Creator `quick_validate.py`: Skill is valid. PyYAML was installed only in the task's scratch validation directory; it is not an application dependency.
- `node --check ai4boji/web/app.js`: passes. Node is used only for this syntax check.
- All checked-in JSON resources parse successfully.

Covered behavior: profile → check-in → plan → log → persistent context; retries without duplicate counting; corrections and history; stale-plan detection; equipment/time adjustments; pain/restriction handling; missing values; date windows; timezone independence; memory expiry/forgetting; HTTP origin, token and host checks.

## Browser

- Created a fresh profile in an isolated test store and generated a five-exercise dumbbell plan.
- Changed available time in the synthetic preview from 30 to 20 minutes; the plan changed from four to three exercises and increased its version.
- Saved one actual session at 18 minutes, retried it, then corrected it to 16 minutes. The UI retained one record. A new CLI process read the same 16 minutes and revision 2.
- Verified English/Chinese switching with the product title unchanged.
- Checked all four pages at **320px in Chinese** and **390px in English**; document width matched the viewport without horizontal overflow.
- Checked the desktop at **1280px**. Chart rendering uses measured container width; mobile tick text remains 11px instead of shrinking a desktop SVG.
- Browser error logs were empty during the completed interaction checks.

## Limits

GitHub Actions is configured for Python 3.9 and 3.12. Deployment outcomes are visible in the repository Actions tab. Automatic Skill discovery still depends on the user's Codex client; the explicit `SKILL.md` fallback is documented. This validates the software workflow, not the medical effectiveness of the training rules. The public GitHub Pages deployment serves synthetic data only. No background scheduler is included.

## Public site and film

- Static build creates its synthetic database in a temporary directory; a dedicated test checks the output contains no SQLite file and only synthetic records.
- Public demo is read-only; form writes and record edits are disabled.
- Landing page defaults to Chinese and supports English.
- Film decoded end to end: exactly 60 seconds, 1800 frames, 1920×1080, H.264 video, stereo AAC audio.
- Six representative film frames were visually inspected. Chinese synthetic narration, original generated music, Chinese captions and an English VTT track are included.
