#!/usr/bin/env python3
"""Minimal, dependency-free LSP client over stdio.

Speaks JSON-RPC 2.0 to language servers (clangd, typescript-language-server,
pyright-langserver) with Content-Length framing. One server process is kept
alive for the duration of a batch; each query is a request/response pair.
Diagnostics and other server notifications are collected but never block
queries.

Facts returned by callers carry the provider name, the semantic flag and the
build context; this module deliberately returns raw LSP primitives so the
semantic code bus can normalize them.
"""
from __future__ import annotations

import json
import queue
import subprocess
import threading
from pathlib import Path
from typing import Any, Optional

_REPO_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "tools" / "lsp",  # canonical repo
    Path.home() / "OneDrive" / "Desktop" / "11vatedTech-Claude-System" / "tools" / "lsp",  # hard fallback
]
TOOLS_LSP = next((p for p in _REPO_CANDIDATES if p.exists()), _REPO_CANDIDATES[0])


class LspError(RuntimeError):
    pass


class _StreamReader:
    """Reads Content-Length framed LSP messages from a byte stream."""

    def __init__(self, stream) -> None:
        self._stream = stream
        self._buf = b""

    def _read_chunk(self, n: int) -> bytes:
        """Read up to *n* bytes without blocking for a full buffer."""
        import os
        try:
            return os.read(self._stream.fileno(), n)
        except OSError:
            return b""

    def read_message(self, timeout: float) -> Optional[dict]:
        deadline = timeout
        while True:
            sep = self._buf.find(b"\r\n\r\n")
            if sep == -1:
                chunk = self._read_chunk(1 << 16)
                if not chunk:
                    return None
                self._buf += chunk
                continue
            header = self._buf[:sep].decode("utf-8", "replace")
            self._buf = self._buf[sep + 4:]
            length = 0
            for line in header.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    length = int(line.split(":", 1)[1].strip())
            while len(self._buf) < length:
                chunk = self._read_chunk(min(1 << 16, length - len(self._buf)))
                if not chunk:
                    return None
                self._buf += chunk
            payload = self._buf[:length]
            self._buf = self._buf[length:]
            try:
                return json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                continue  # skip malformed frames; do not kill the session


class LspClient:
    """JSON-RPC session against one language server process."""

    def __init__(self, cmd: list[str], cwd: Path, name: str, timeout: float = 60.0) -> None:
        self.name = name
        self.timeout = timeout
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._reader = _StreamReader(self._proc.stdout)
        self._queue: queue.Queue[dict] = queue.Queue()
        self._next_id = 1
        self._closed = False
        self._thread = threading.Thread(target=self._pump, daemon=True)
        # Do NOT start the pump yet — LSP requires the client to send
        # initialize first, so the server won't speak until we do.

    def _start_pump(self) -> None:
        self._thread.start()

    def _pump(self) -> None:
        while True:
            try:
                message = self._reader.read_message(self.timeout)
            except Exception:
                return
            if message is None:
                return
            self._queue.put(message)

    def _send(self, method: str, params: dict, id_: Optional[int] = None) -> None:
        if self._closed:
            raise LspError(f"{self.name}: server closed")
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
        if id_ is not None:
            message["id"] = id_
        body = json.dumps(message).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self._proc.stdin.write(header + body)
        self._proc.stdin.flush()

    def _request(self, method: str, params: dict) -> dict:
        request_id = self._next_id
        self._next_id += 1
        self._send(method, params, id_=request_id)
        while True:
            try:
                message = self._queue.get(timeout=self.timeout)
            except queue.Empty:
                raise LspError(f"{self.name}.{method}: no response within {self.timeout}s")
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise LspError(f"{self.name}.{method}: {message['error'].get('message', message['error'])}")
            return message.get("result") or {}

    def initialize(self, root_uri: str, capabilities: Optional[dict] = None) -> None:
        self._start_pump()
        result = self._request(
            "initialize",
            {
                "processId": None,
                "rootUri": root_uri,
                "capabilities": capabilities or {"workspace": {"symbol": {"dynamicRegistration": False}}},
            },
        )
        self._send("initialized", {"params": {}})
        self.server_info = result

    def open_document(self, uri: str, language_id: str, text: str) -> None:
        self._send("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": language_id, "version": 1, "text": text}})

    def workspace_symbols(self, query: str) -> list[dict]:
        return self._request("workspace/symbol", {"query": query})

    def document_symbols(self, uri: str) -> list[dict]:
        return self._request("textDocument/documentSymbol", {"textDocument": {"uri": uri}})

    def definition(self, uri: str, line: int, character: int) -> list[dict]:
        return self._request(
            "textDocument/definition", {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        )

    def type_definition(self, uri: str, line: int, character: int) -> list[dict]:
        return self._request(
            "textDocument/typeDefinition", {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}
        )

    def references(self, uri: str, line: int, character: int) -> list[dict]:
        return self._request(
            "textDocument/references",
            {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}, "context": {"includeDeclaration": False}},
        )

    def hover(self, uri: str, line: int, character: int) -> dict:
        return self._request("textDocument/hover", {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}})

    def shutdown(self) -> None:
        if self._closed:
            return
        try:
            self._request("shutdown", {})
        except Exception:
            pass
        try:
            self._send("exit", {})
        except Exception:
            pass
        self._closed = True
        self._proc.terminate()
        try:
            self._proc.wait(timeout=5)
        except Exception:
            self._proc.kill()


# ---------------------------------------------------------------------------
# Provider spawn recipes
# ---------------------------------------------------------------------------


def utf16_col(line_text: str, char_index: int) -> int:
    """Convert a Python char offset within a line to an LSP UTF-16 column."""
    col = 0
    for ch in line_text[:char_index]:
        col += 2 if ord(ch) > 0xFFFF else 1
    return col


def char_col_from_utf16(line_text: str, utf16_col_: int) -> int:
    col = 0
    for index, ch in enumerate(line_text):
        width = 2 if ord(ch) > 0xFFFF else 1
        if col + width > utf16_col_:
            return index
        col += width
    return len(line_text)


def provider_command(lang: str, root: Path, compile_commands_dir: Optional[Path] = None) -> tuple[list[str], Path]:
    node = "node"
    if lang == "cpp":
        clangd = TOOLS_LSP / "clangd-dist" / "clangd_22.1.6" / "bin" / "clangd.exe"
        cmd = [str(clangd), "--header-insertion=never"]
        if compile_commands_dir:
            cmd.append(f"--compile-commands-dir={compile_commands_dir}")
        return cmd, root
    if lang == "ts":
        return [node, str(TOOLS_LSP / "node_modules" / "typescript-language-server" / "lib" / "cli.mjs"), "--stdio"], TOOLS_LSP
    if lang == "py":
        return [node, str(TOOLS_LSP / "node_modules" / "pyright" / "dist" / "pyright-langserver.js"), "--stdio", "--logfile", str(root / ".pyright-lsp.log")], root
    raise LspError(f"no provider for language {lang}")


def language_id_for(lang: str) -> str:
    return {"cpp": "cpp", "ts": "typescript", "py": "python"}[lang]


def to_uri(path: Path) -> str:
    return path.resolve().as_uri()