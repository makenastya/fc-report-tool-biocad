"""
Запуск инструмента из консоли.

- Для запуска как модуль (python -m fctool ./data_dir) см fctool.__main__.py
- Для запуска командой (python -m fctool ./data_dir) см pyproject.toml
  секцию [tool.poetry.scripts]
"""

import argparse
from pathlib import Path
from typing import Dict
import yaml
from fctool.main import process_tables


def parse_yaml(yfile: Path) -> Dict:
    with open(yfile, 'r', encoding='utf8') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
        return config


def run():
    parser = argparse.ArgumentParser(description="Запускает скрипт")

    # Все что начинается с минуса - это ключ
    parser.add_argument("--config",
                        help="Путь до файла конфига. "
                             "По умолчанию ищет config.yaml внутри папки с данными.",
                        dest="config_path",
                        type=Path,
                        required=False,
                        default=None)
    parser.add_argument("--out",
                        help="Путь до папки с обработанными данными. "
                             "По умолчанию сохраняет в папку Output_date_time в текущем расположении.",
                        dest="out_path",
                        type=Path,
                        required=False,
                        default=None)
    parser.add_argument("--round",
                        help="On - если нужно округление рассчитаных значений, иначе не указывать.",
                        dest="round_key",
                        type=bool,
                        required=False,
                        default=False
                        )
    # это просто позиционный аргумент
    parser.add_argument("tables_dir",
                        help="Путь до папки, содержащей данные",
                        type=Path)

    args = parser.parse_args()
    if args.config_path is None:
        args.config_path = args.tables_dir / "config.yaml"
    if args.out_path is None:
        args.out_path = Path('.')

    args.config_path = args.config_path.absolute()
    args.tables_dir = args.tables_dir.absolute()
    args.out_path = args.out_path.absolute()

    if not args.tables_dir.exists():
        raise ValueError(f"Путь до папки с данными '{args.tables_dir}' не существует")

    if not args.config_path.exists():
        raise ValueError(f"Путь до конфига '{args.config_path}' не существует. "
                         f"Поместите config.yaml в папку с данными либо укажите путь до конфига.")
    config = parse_yaml(args.config_path)
    cv = config['cv']
    percent = config['percent']
    lloq = config['lloq']
    min_events = config['min_events']
    points = config['points']
    populations = config['populations']
    cytometer = config['cytometer']

    process_tables(args.tables_dir, args.out_path, cytometer, populations, percent, cv, lloq, min_events, points, args.round_key)