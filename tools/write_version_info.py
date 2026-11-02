from __future__ import annotations

import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build_version_info.txt"


def version_parts(label: str) -> tuple[int, int, int, int]:
    nums = [int(value) for value in re.findall(r"\d+", label)[:4]]
    return tuple((nums + [0, 0, 0, 0])[:4])


def tuple_text(parts: tuple[int, int, int, int]) -> str:
    return ", ".join(str(value) for value in parts)


def main() -> None:
    label = os.environ.get("SOLITAIRE_VERSION", "dev").strip() or "dev"
    parts = version_parts(label)
    numeric = ".".join(str(value) for value in parts)

    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple_text(parts)}),
    prodvers=({tuple_text(parts)}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('FileDescription', 'Solitaire+'),
          StringStruct('FileVersion', '{numeric}'),
          StringStruct('InternalName', 'Simple Solitaire'),
          StringStruct('OriginalFilename', 'Simple Solitaire.exe'),
          StringStruct('ProductName', 'Solitaire+'),
          StringStruct('ProductVersion', '{label}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT.name} for {label}")


if __name__ == "__main__":
    main()
