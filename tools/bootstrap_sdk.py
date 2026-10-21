"""Install a verified official SDK bundle into the pinned tools' local caches."""

from pathlib import Path
import hashlib
import shutil
import tempfile
import urllib.request

VERSION = "v0.3.0-rc7"
URL = "https://github.com/genlayerlabs/genvm/releases/download/v0.3.0-rc7/genvm-runners-all.tar.xz"
SHA256 = "e218a1854214681560351051f76fe2b878545cf3409455ef372d57014a88ca67"
NAME = f"genvm-universal-{VERSION}.tar.xz"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    targets = [Path.home() / ".cache" / tool / NAME for tool in ("gltest-direct", "genvm-linter")]
    source = next((p for p in targets if p.is_file() and digest(p) == SHA256), None)
    if source is None:
        targets[0].parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=targets[0].parent, delete=False) as handle:
            partial = Path(handle.name)
            try:
                with urllib.request.urlopen(URL, timeout=30) as response:
                    shutil.copyfileobj(response, handle)
            except BaseException:
                partial.unlink(missing_ok=True)
                raise
        if digest(partial) != SHA256:
            partial.unlink()
            raise RuntimeError("Official SDK checksum mismatch; no cache entry installed")
        partial.replace(targets[0])
        source = targets[0]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target != source and (not target.is_file() or digest(target) != SHA256):
            shutil.copy2(source, target)
    print(f"Verified GenVM {VERSION}: {SHA256}")


if __name__ == "__main__":
    main()
