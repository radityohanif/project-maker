from __future__ import annotations

import hashlib
import tempfile
import urllib.request
from pathlib import Path

from deck_maker.core.models import DeckImageSource


def resolve_image_path(
    source: DeckImageSource,
    *,
    base_dir: Path,
    allow_network: bool,
) -> Path:
    """Return a filesystem path to image bytes (downloads URLs when allowed)."""
    if source.path is not None:
        resolved = (base_dir / source.path).resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Image not found: {resolved}")
        return resolved

    if source.url is not None:
        if not allow_network:
            raise ValueError(
                "Remote image in deck requires presentation.allow_network: true "
                f"(or pass allow_network when rendering). URL: {source.url}"
            )
        req = urllib.request.Request(source.url, headers={"User-Agent": "deck-maker/0.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - opt-in
            data = resp.read()
        suffix = Path(source.url).suffix or ".png"
        if suffix.lower() not in (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tif",
            ".tiff",
            ".webp",
        ):
            suffix = ".png"
        digest = hashlib.sha1(data, usedforsecurity=False).hexdigest()[:16]
        tmp = Path(tempfile.gettempdir()) / f"deck-maker-remote-{digest}{suffix}"
        tmp.write_bytes(data)
        return tmp

    raise ValueError("Image source has neither path nor url.")


def cleanup_temp_remote(path: Path) -> None:
    """Best-effort delete for files under the system temp directory."""
    try:
        temp_root = Path(tempfile.gettempdir()).resolve()
        resolved = path.resolve()
        if temp_root in resolved.parents or resolved.parent == temp_root:
            path.unlink(missing_ok=True)
    except OSError:
        pass
