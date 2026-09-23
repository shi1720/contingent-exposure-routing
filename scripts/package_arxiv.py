"""Create a minimal, portable LaTeX source package; does not submit to arXiv."""
from pathlib import Path
import shutil
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'submission/arxiv-source.tar.gz'
    with tempfile.TemporaryDirectory(prefix='cer-arxiv-') as directory:
        stage = Path(directory)
        source = (ROOT / 'paper/main.tex').read_text()
        (stage / 'main.tex').write_text(source.replace(
            r'\graphicspath{{../figures/}}', r'\graphicspath{{figures/}}'))
        for name in ['references.bib', 'main.bbl', 'model-table.tex',
                     'synthetic-table.tex', 'api-table.tex']:
            shutil.copy2(ROOT / 'paper' / name, stage / name)
        (stage / 'figures').mkdir()
        for path in sorted((ROOT / 'figures').glob('*.pdf')):
            shutil.copy2(path, stage / 'figures' / path.name)
        (stage / 'README.txt').write_text(
            'Contingent Exposure Routing for Financial AI\n'
            'Shivam Gupta\n\n'
            'Main file: main.tex. Compile with pdfLaTeX and BibTeX, or Tectonic.\n'
            'A generated main.bbl is included. Six figures are vector PDFs.\n'
            'Manuscript and constructed research data: CC BY 4.0.\n'
            'Code and complete data: https://github.com/shi1720/contingent-exposure-routing\n'
            'This package is prepared source, not evidence of submission or acceptance.\n')
        with tarfile.open(output, 'w:gz') as archive:
            for path in sorted(stage.rglob('*')):
                if path.is_file():
                    archive.add(path, arcname=path.relative_to(stage))
    print(output)


if __name__ == '__main__':
    main()
