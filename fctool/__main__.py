"""
python3 -m fctool запустит этот модуль
"""

import argparse
from pathlib import Path
from typing import Dict

import yaml


def parse_yaml(yfile: Path) -> Dict:
    with open(yfile, 'r', encoding='utf8') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Запускает скрипт")

    # Все что начинается с минуса - это ключ
    parser.add_argument("--config",
                        help="Путь до файла конфига. "
                             "По умолчанию ищет config.yaml внутри папки с данными.",
                        dest="config_path",
                        type=Path,
                        required=False,
                        default=None)

    # это просто позиционный аргумент
    parser.add_argument("tables_dir",
                        help="Путь до папки, содержащей ДОПИШИ ОПИСАНИЕ",
                        type=Path)

    args = parser.parse_args()

    if args.config_path is None:
        args.config_path = args.tables_dir / "config.yaml"

    args.config_path = args.config_path.absolute()
    args.tables_dir = args.tables_dir.absolute()

    if not args.tables_dir.exists():
        raise ValueError(f"Путь до папки с данными '{args.tables_dir}' не существует")

    if not args.config_path.exists():
        raise ValueError(f"Путь до конфига '{args.config_path}' не существует. "
                         f"Поместите config.yaml в папку с данными либо укажите путь до конфига.")

