from __future__ import annotations

import io
import shutil
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

import platformdirs

GITHUB_OWNER = "npechl"
GITHUB_REPO = "pdbe-bioskills"
GITHUB_BRANCH = "main"

_FOLDERS = ("skills", "profiles")


def cache_dir() -> Path:
    return Path(platformdirs.user_cache_dir("pdbe-bioskills"))


def content_dir() -> Path:
    return cache_dir() / "content"


def is_cached() -> bool:
    d = content_dir()
    return all((d / f).is_dir() for f in _FOLDERS)


def fetch(force: bool = False) -> None:
    if not force and is_cached():
        return

    url = (
        f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/archive/refs/heads/{GITHUB_BRANCH}.tar.gz"
    )

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Failed to fetch content from GitHub: {exc}\n"
            "Check your internet connection and try again with: pdbe-bioskills update"
        ) from exc

    dest = content_dir()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    prefix = f"{GITHUB_REPO}-{GITHUB_BRANCH}/"
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        _extract_folders(tar, dest, prefix, _FOLDERS)


def _extract_folders(
    tar: tarfile.TarFile,
    dest: Path,
    strip_prefix: str,
    folders: tuple[str, ...],
) -> None:
    dest_resolved = dest.resolve()
    for member in tar.getmembers():
        for folder in folders:
            if not member.name.startswith(f"{strip_prefix}{folder}/"):
                continue
            rel_path = member.name[len(strip_prefix):]
            if not rel_path:
                continue
            target = dest / rel_path
            try:
                target.resolve().relative_to(dest_resolved)
            except ValueError:
                continue
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                f = tar.extractfile(member)
                if f is not None:
                    target.write_bytes(f.read())
            break
