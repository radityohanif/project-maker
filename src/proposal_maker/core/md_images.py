"""Markdown image extraction: inline, reference-style, and base64 data URIs.

The Markdown-it reference resolver collapses ``![alt][id]`` into an inline
``image`` token whose ``src`` attribute is the resolved destination (which may
be a ``data:`` URI). This module converts those tokens into
:class:`ImageBlock` instances.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from pathlib import Path

from markdown_it.token import Token

from proposal_maker.core.models import ImageBlock

_DATA_URI_RE = re.compile(
    r"^data:image/(?P<ext>[a-zA-Z0-9.+-]+)(?P<params>;[^,]*)?,(?P<payload>.+)$",
    re.DOTALL,
)

_EXT_ALIASES = {
    "jpeg": "jpg",
    "svg+xml": "svg",
    "x-icon": "ico",
    "vnd.microsoft.icon": "ico",
}


def image_token_to_block(
    token: Token,
    *,
    md_dir: Path,
    image_cache_dir: Path,
) -> ImageBlock | None:
    """Convert a markdown-it ``image`` inline token to an :class:`ImageBlock`.

    - Data URIs (``data:image/png;base64,...``) are decoded and written to
      ``image_cache_dir`` as ``img-<sha1>.<ext>``.
    - Bare ``http(s)://`` URLs become ``ImageBlock(url=...)`` for the renderer
      to handle (only when ``--allow-network`` is set).
    - Everything else is treated as a path relative to the MD file directory.
    Returns ``None`` if the source cannot be interpreted.
    """
    src = _attr(token, "src")
    if not src:
        return None

    alt = _image_alt(token)
    ref_id = _attr(token, "id")
    caption = _attr(token, "title") or None

    if src.startswith("data:"):
        path = _decode_data_uri(src, image_cache_dir)
        if path is None:
            return None
        return ImageBlock(path=path, alt=alt, id=ref_id, caption=caption)

    if src.startswith(("http://", "https://")):
        return ImageBlock(url=src, alt=alt, id=ref_id, caption=caption)

    candidate = (md_dir / src).resolve()
    return ImageBlock(path=candidate, alt=alt, id=ref_id, caption=caption)


def _image_alt(token: Token) -> str | None:
    alt_attr = _attr(token, "alt")
    if alt_attr:
        return alt_attr
    if token.children:
        text = "".join(c.content for c in token.children if c.type == "text")
        return text or None
    if token.content:
        return token.content
    return None


def _attr(token: Token, name: str) -> str | None:
    attrs = getattr(token, "attrs", None) or {}
    if isinstance(attrs, dict):
        for key, value in attrs.items():
            if key == name:
                return value
    else:
        for key, value in attrs:
            if key == name:
                return value
    return None


def _decode_data_uri(uri: str, out_dir: Path) -> Path | None:
    match = _DATA_URI_RE.match(uri.strip())
    if not match:
        return None
    ext = match.group("ext").lower()
    ext = _EXT_ALIASES.get(ext, ext)
    params = (match.group("params") or "").lower()
    payload = match.group("payload")
    try:
        if ";base64" in params:
            data = base64.b64decode(payload, validate=False)
        else:
            from urllib.parse import unquote_to_bytes

            data = unquote_to_bytes(payload)
    except (binascii.Error, ValueError):
        return None
    digest = hashlib.sha1(data, usedforsecurity=False).hexdigest()[:16]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"img-{digest}.{ext}"
    if not out_path.exists():
        out_path.write_bytes(data)
    return out_path
