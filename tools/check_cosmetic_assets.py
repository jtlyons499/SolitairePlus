"""Run from the project with: python tools/check_cosmetic_assets.py"""
import csv
from pathlib import Path
import sys
import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from settings import MENU_BACKGROUNDS, FELTS, TITLES


def audit_catalogs():
    rows = []
    for kind, catalog in [('backgrounds', MENU_BACKGROUNDS), ('felts', FELTS), ('titles', TITLES)]:
        for key, data in sorted(catalog.items(), key=lambda pair: (pair[1].get('order', 9999), pair[0])):
            path = ROOT / data['path']
            width = height = ''
            error = ''
            if not path.is_file():
                status = 'MISSING'
            else:
                try:
                    image = pygame.image.load(str(path))
                    width, height = image.get_size()
                    status = 'OK'
                except (OSError, pygame.error) as exc:
                    status, error = 'UNREADABLE', str(exc)
            rows.append(dict(kind=kind, asset_id=key, current_name=data.get('name', key),
                             path=data['path'], rating_category=data.get('rating_category', ''),
                             rating_threshold=data.get('rating_threshold', ''), width=width, height=height,
                             status=status, error=error, new_filename='', new_display_name=''))
    return rows


def main():
    rows = audit_catalogs()
    destination = ROOT / 'COSMETIC_ASSET_REPORT.csv'
    with destination.open('w', newline='', encoding='utf-8-sig') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    for status in ('OK', 'MISSING', 'UNREADABLE'):
        print(f'{status}: {sum(row["status"] == status for row in rows)}')
    print(f'Report: {destination}')
    print('Optional: fill new_filename and new_display_name, then send the CSV for the naming pass.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
