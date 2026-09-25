from __future__ import annotations

import base64
import io

import requests


def post_update(url: str | None, payload: dict, frame=None) -> None:
    if not url:
        return
    body = dict(payload)
    if frame is not None:
        buffer = io.BytesIO()
        frame.save(buffer, format="JPEG", quality=72)
        body["frame"] = base64.b64encode(buffer.getvalue()).decode("ascii")
    try:
        requests.post(f"{url.rstrip('/')}/api/update", json=body, timeout=2)
    except requests.RequestException:
        # A dashboard outage must never stop a team's run.
        pass

