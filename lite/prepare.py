#!/usr/bin/env python3
"""Restore verified Fiction Lite locally from the Git-tracked compressed snapshot.

Run from the repository root: python lite/prepare.py
No network, package dependencies, or original 199 MiB Full database required.
"""
from __future__ import annotations

import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'fiction_retail_lite.sqlite.xz'
DEST = ROOT / 'fiction_retail_lite.sqlite'
MANIFEST = ROOT / 'manifest_lite.json'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as reader:
        for chunk in iter(lambda: reader.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    expected = manifest['runtime_sha256']
    if not ARCHIVE.is_file():
        raise SystemExit(f'Missing compressed Fiction Lite: {ARCHIVE}')
    if digest(ARCHIVE) != '8eae82668a140281eedcb9a438bd71c7729fd82e17a48254ca77dfa0ec1c37f6':
        raise SystemExit('Compressed Fiction Lite has an unexpected SHA-256')
    if DEST.exists():
        if digest(DEST) != expected:
            raise SystemExit('Existing Lite SQLite differs from manifest; refusing to overwrite')
        print('SQLite already present and checksum verified')
    else:
        temporary = DEST.with_name(DEST.name + '.tmp')
        if temporary.exists():
            raise SystemExit('Temporary output already exists; clean up manually after inspection')
        try:
            with lzma.open(ARCHIVE, 'rb') as compressed, temporary.open('xb') as writer:
                for chunk in iter(lambda: compressed.read(1024 * 1024), b''):
                    writer.write(chunk)
            if digest(temporary) != expected:
                raise ValueError('Decompressed SQLite SHA-256 does not match the pinned manifest')
            temporary.replace(DEST)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        print(f'Restored {DEST.name}: {DEST.stat().st_size:,} bytes')

    from build_knowledge import main as install_knowledge
    from verify_fiction_lite import verify

    install_knowledge()
    result = verify()
    print(f'PASS {len(result["gates"])} verification gates; source SHA-256 {expected}')
    print('Fiction Full is unchanged; Full-release oracles are not interchangeable with Lite.')


if __name__ == '__main__':
    main()