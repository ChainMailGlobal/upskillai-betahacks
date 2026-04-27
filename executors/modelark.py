from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ModelArkError(RuntimeError):
    pass


class ModelArkClient:
    def __init__(self, api_key: str, base_url: str, timeout_sec: float = 120.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._url(path),
            data=body,
            method="POST",
            headers=self._headers({"Content-Type": "application/json"}),
        )
        return self._read_json(request)

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._url(path)
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"
        request = urllib.request.Request(url, method="GET", headers=self._headers())
        return self._read_json(request)

    def post_multipart(
        self,
        path: str,
        fields: dict[str, str],
        file_field: str,
        file_path: Path,
    ) -> dict[str, Any]:
        boundary = f"----upskillai-{uuid.uuid4().hex}"
        chunks: list[bytes] = []

        for key, value in fields.items():
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                    value.encode("utf-8"),
                    b"\r\n",
                ]
            )

        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{file_field}"; '
                    f'filename="{file_path.name}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
                file_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )

        request = urllib.request.Request(
            self._url(path),
            data=b"".join(chunks),
            method="POST",
            headers=self._headers({"Content-Type": f"multipart/form-data; boundary={boundary}"}),
        )
        return self._read_json(request)

    def post_json_bytes(self, path: str, payload: dict[str, Any]) -> bytes:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._url(path),
            data=body,
            method="POST",
            headers=self._headers({"Content-Type": "application/json"}),
        )
        return self._read_bytes(request)

    def download_file(self, url: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                output_path.write_bytes(response.read())
        except urllib.error.URLError as exc:
            raise ModelArkError(f"Download failed for {url}: {exc}") from exc
        return output_path

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if extra:
            headers.update(extra)
        return headers

    def _read_json(self, request: urllib.request.Request) -> dict[str, Any]:
        raw = self._read_bytes(request)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ModelArkError(f"Expected JSON response, got: {raw[:300]!r}") from exc

    def _read_bytes(self, request: urllib.request.Request) -> bytes:
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ModelArkError(f"HTTP {exc.code} from {request.full_url}: {body}") from exc
        except urllib.error.URLError as exc:
            raise ModelArkError(f"Request failed for {request.full_url}: {exc}") from exc
