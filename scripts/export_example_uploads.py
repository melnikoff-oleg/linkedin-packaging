"""Export approved example upload files, grouped by person and reference style."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_example_pack import ROOT, DOWNLOADS, STYLES, accepted, sha


def export_uploads(accounts, output):
    entries = []
    for account in accounts:
        folder = ROOT / 'examples' / account
        if folder.parent != ROOT / 'examples' or not folder.is_dir():
            raise ValueError('Unknown example account')
        manifest = json.loads((folder / 'manifest.json').read_text())
        rows = {row['style']: row for row in manifest['packages']}
        if set(rows) != set(STYLES) or len(manifest['packages']) != len(STYLES):
            raise ValueError('All ten finalized styles are required')
        for style, row in rows.items():
            if not accepted(folder, style):
                raise ValueError(f'Current source and independent reviews required: {account}/{style}')
            for name in DOWNLOADS:
                path = folder / 'results' / style / name
                if sha(path) != row['sha256'].get(name):
                    raise ValueError(f'Finalized upload changed: {account}/{style}/{name}')
                entries.append((f'{account}/{style}/{name}', path.read_bytes()))
    readme = ('LinkedIn profile packages\n\n'
              'Each person has ten reference styles. Each style folder contains:\n'
              'banner.png — LinkedIn banner\nportrait.png — profile photo\n'
              'headline.txt — proposed headline\npreview.png — assembled local preview\n\n'
              'Choose one complete style per person. Inspect LinkedIn’s final upload crop.\n'
              'These are proposed designs with AI-edited portraits; no account was published or changed.\n'
              'Source evidence, original comparisons, mobile previews and independent AI review records\n'
              'are retained in the full project under examples/. AI reviews are simulations, not human interviews.\n')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in [('README.txt', readme.encode()), *sorted(entries)]:
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account', action='append', dest='accounts')
    parser.add_argument('--output', default=str(ROOT / 'dist/kayla-emily-linkedin-packages.zip'))
    args = parser.parse_args()
    print(export_uploads(args.accounts or ['kayla', 'emily'], args.output))
