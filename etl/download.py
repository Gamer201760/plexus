"""Скачать и распаковать источники в data/raw/<name>/. Повторный запуск пропускает скачанное."""
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sources import SOURCES

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def fetch(name: str, url: str) -> None:
    dst = RAW / name
    if dst.exists() and any(dst.iterdir()):
        print(f"skip  {name}")
        return
    dst.mkdir(parents=True, exist_ok=True)
    archive = RAW / f"{name}.zip"
    print(f"get   {name}")
    urllib.request.urlretrieve(url, archive)
    with zipfile.ZipFile(archive) as z:
        for m in z.infolist():
            target = (dst / m.filename).resolve()
            if not target.is_relative_to(dst.resolve()):  # защита от zip-slip
                raise ValueError(f"bad path in archive: {m.filename}")
        z.extractall(dst)
    archive.unlink()
    prune(dst)


def prune(dst: Path) -> None:
    """Если есть parquet — CSV/XLSX и *_parts дублируют его (до 9 ГБ). Удалить их и мусор macOS."""
    shutil.rmtree(dst / "__MACOSX", ignore_errors=True)
    if not any(dst.glob("*.parquet")):
        return
    for p in dst.iterdir():
        if p.is_dir() and p.name.endswith("_parts"):
            shutil.rmtree(p)
        elif p.suffix in (".csv", ".xlsx"):
            p.unlink()


if __name__ == "__main__":
    names = sys.argv[1:] or list(SOURCES)
    for n in names:
        fetch(n, SOURCES[n])
