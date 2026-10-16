# AI4薄肌

60 秒项目宣传片 / 60-second product film.

- `AI4薄肌-60s.mp4`: 1920 × 1080, 30 fps, H.264/AAC; Chinese narration and burned-in Chinese captions.
- `promo-poster.jpg`: video cover.
- `promo-zh.srt`, `promo-zh.vtt`, `promo-en.vtt`: editable captions; the website offers the English subtitle track.
- Graphics and music are generated specifically for this project. Product screenshots contain synthetic demo data. Narration uses the macOS Tingting synthetic voice. No stock footage or third-party music is included.
- Font files and the speech engine are system dependencies and are not redistributed.

Rebuild on macOS, with a Chinese PingFang font and Tingting voice installed:

```bash
python3 -m venv work/media-env
work/media-env/bin/pip install pillow numpy imageio-ffmpeg
work/media-env/bin/python scripts/make_promo.py --work work/promo-render
```

Use `--font /path/to/font.ttc` to select another Chinese font. The app itself remains standard-library-only. The film introduces v0.1 capabilities; it makes no promise about body transformation or medical outcomes.
