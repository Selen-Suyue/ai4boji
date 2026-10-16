"""Build the public site using only synthetic, temporary records."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ai4boji.core import Service, seed_demo
from ai4boji.storage import Store


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'site', destination, dirs_exist_ok=True)
    assets = destination / 'assets'
    assets.mkdir(exist_ok=True)
    for name in ['dashboard-zh.jpg', 'progress-zh.jpg']:
        shutil.copy2(ROOT / 'docs/previews' / name, assets / name)
    for file in (ROOT / 'media').glob('*'):
        if file.suffix in {'.mp4', '.jpg', '.vtt'}:
            shutil.copy2(file, assets / file.name)
    demo = destination / 'demo'
    shutil.copytree(ROOT / 'ai4boji/web', demo, dirs_exist_ok=True)
    # Never read data/ or .demo/: each build creates its own synthetic store.
    with tempfile.TemporaryDirectory() as tmp:
        service = Service(Store(tmp))
        seed_demo(service)
        today = service.today()
        dates = [d['date'] for d in service.report(today, 14)['calendar']]
        states = {d: dict(service.state(d), demo=True) for d in dates}
    (demo / 'states.json').write_text(json.dumps(states, ensure_ascii=False), encoding='utf-8')
    (demo / 'preview.js').write_text('''
'use strict';
const previewStates = fetch('./states.json').then(r => {if(!r.ok)throw Error('Preview unavailable');return r.json();});
window.AI4BOJI_PREVIEW = async (path,data) => {
  if(data !== undefined) throw Error('线上为只读演示，请下载后本地使用。 / Run locally to save records.');
  if(!path.startsWith('state')) throw Error('只读演示 / Read-only preview');
  const states=await previewStates, dates=Object.keys(states).sort();
  const day=new URLSearchParams(path.split('?')[1]||'').get('date')||dates.at(-1);
  if(!states[day])throw Error('请选择演示日历中的日期 / Choose a date in the demo calendar');
  return structuredClone(states[day]);
};
''', encoding='utf-8')
    html = (demo / 'index.html').read_text()
    html = html.replace('href="/style.css"', 'href="./style.css"').replace('src="/app.js"', 'src="./app.js"')
    html = html.replace('<script src="./app.js"', '<script src="./preview.js" defer></script>\n  <script src="./app.js"')
    (demo / 'index.html').write_text(html, encoding='utf-8')
    (destination / '.nojekyll').touch()
    print('Built synthetic public site:', destination)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'dist')
