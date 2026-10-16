"""Run from the repository: python3 -m ai4boji --help."""
import argparse
import json
import sys
from pathlib import Path

from .catalog import localize
from .core import Service, seed_demo
from .storage import Store


ROOT = Path.cwd()


def read_input(path):
    if path == '-':
        return json.load(sys.stdin)
    with open(path, encoding='utf-8') as stream:
        return json.load(stream)


def markdown_report(report, lang='zh-CN'):
    labels = ['训练天数', '训练分钟', '未记录天数', '记录依据'] if lang == 'zh-CN' else ['Training days', 'Training minutes', 'Unrecorded days', 'Source IDs']
    return '\n'.join(['# AI4薄肌', '', report['start'] + ' → ' + report['end'], '',
        f"- {labels[0]}: {report['training_days']}",
        f"- {labels[1]}: {report['total_minutes']}",
        f"- {labels[2]}: {report['unknown_days']}", '', report['reflection'], '',
        labels[3] + ': ' + ', '.join(report['source_ids'])])


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python3 -m ai4boji', description='AI4薄肌 — 本地训练档案与 Codex 工具 / Local training memory and Codex tools')
    parser.add_argument('--data-dir', help='私有数据目录 / Private data directory')
    parser.add_argument('--lang', choices=['zh-CN', 'en'], default='zh-CN')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['profile', 'checkin', 'log', 'memory']:
        p = sub.add_parser(name, help='通过 JSON 保存 / Save JSON')
        p.add_argument('--input', default='-', help='JSON 文件或 - 表示 stdin / JSON file or - for stdin')
    for name in ['context', 'state', 'plan']:
        p = sub.add_parser(name)
        p.add_argument('--date')
    p = sub.add_parser('report')
    p.add_argument('--date')
    p.add_argument('--days', type=int, default=7)
    p.add_argument('--format', choices=['json', 'markdown'], default='json')
    p = sub.add_parser('history')
    p.add_argument('id')
    p = sub.add_parser('forget')
    p.add_argument('id')
    sub.add_parser('export')
    sub.add_parser('demo', help='建立隔离的合成演示 / Create isolated synthetic demo')
    p = sub.add_parser('serve', help='启动本地面板 / Start local dashboard')
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--demo', action='store_true')
    args = parser.parse_args(argv)
    demo = args.command == 'demo' or (args.command == 'serve' and args.demo)
    directory = args.data_dir or ROOT / ('.demo' if demo else 'data')
    try:
        service = Service(Store(directory))
        if demo:
            seed_demo(service)
        command = args.command
        if command == 'serve':
            from .server import run
            run(service, args.port, demo)
            return 0
        if command in ['profile', 'checkin', 'log', 'memory']:
            result = getattr(service, 'save_' + command)(read_input(args.input))
        elif command == 'plan':
            result = service.generate_plan(args.date)
        elif command in ['context', 'state']:
            result = getattr(service, command)(args.date)
        elif command == 'report':
            result = localize(service.report(args.date, args.days), args.lang)
            if args.format == 'markdown':
                print(markdown_report(result, args.lang))
                return 0
        elif command == 'history':
            result = service.store.history(args.id)
        elif command == 'forget':
            result = service.store.forget(args.id)
        elif command == 'export':
            result = service.store.export()
        else:
            result = {'title': 'AI4薄肌', 'demo': True, 'data_dir': str(service.store.directory), 'next': 'python3 -m ai4boji serve --demo'}
        # Export/state preserve bilingual source structures for portability.
        if command not in ['export', 'state']:
            result = localize(result, args.lang)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
