#!/usr/bin/env python3
"""Windows path/environment resolution for Unreal Foundry tools.

Git Bash, PowerShell, cmd.exe, Python launchers, and Claude wrappers can expose
slightly different environment variables. Unreal validation must resolve known
Windows folders from Windows APIs first, then use deterministic fallbacks.
"""
from __future__ import annotations

import ctypes
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any


KNOWN_FOLDER_GUIDS = {
    "USERPROFILE": "{5E6C858F-0E22-4760-9AFE-EA3317B67173}",
    "APPDATA": "{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}",
    "LOCALAPPDATA": "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}",
    "ProgramFiles": "{905e63b6-c1bf-494e-b29c-65b732d3d21a}",
    "ProgramFiles(x86)": "{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}",
}


@dataclass(frozen=True)
class ResolvedPath:
    name: str
    path: str
    source: str
    exists: bool

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "path": self.path, "source": self.source, "exists": self.exists}


def _normalize_windows_path(path: str | os.PathLike[str]) -> str:
    text = str(path).strip().strip('"')
    if not text:
        return ""
    converted = git_bash_to_windows(text)
    # PureWindowsPath preserves drive semantics even when called from MSYS Python.
    win = PureWindowsPath(converted)
    return str(win).replace("/", "\\")


def _existing(path: str) -> bool:
    try:
        return Path(path).exists()
    except OSError:
        return False


def _known_folder(name: str) -> ResolvedPath | None:
    guid_text = KNOWN_FOLDER_GUIDS.get(name)
    if os.name != "nt" or not guid_text:
        return None
    try:
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]

        ole32 = ctypes.windll.ole32
        shell32 = ctypes.windll.shell32
        guid = GUID()
        if ole32.CLSIDFromString(ctypes.c_wchar_p(guid_text), ctypes.byref(guid)) != 0:
            return None
        out = ctypes.c_wchar_p()
        # KF_FLAG_DEFAULT = 0, token = NULL
        hr = shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(out))
        if hr != 0 or not out.value:
            return None
        try:
            path = _normalize_windows_path(out.value)
            return ResolvedPath(name, path, "SHGetKnownFolderPath", _existing(path))
        finally:
            ole32.CoTaskMemFree(out)
    except Exception:
        return None


def _get_temp_path() -> ResolvedPath | None:
    if os.name == "nt":
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            length = ctypes.windll.kernel32.GetTempPathW(len(buffer), buffer)
            if length:
                path = _normalize_windows_path(buffer.value)
                return ResolvedPath("TEMP", path, "GetTempPathW", _existing(path))
        except Exception:
            pass
    env = os.environ.get("TEMP") or os.environ.get("TMP") or tempfile.gettempdir()
    if env:
        path = _normalize_windows_path(env)
        return ResolvedPath("TEMP", path, "environment" if os.environ.get("TEMP") or os.environ.get("TMP") else "tempfile", _existing(path))
    return None


def resolve_known_path(name: str) -> ResolvedPath:
    if name == "TEMP":
        resolved = _get_temp_path()
        if resolved:
            return resolved
    api = _known_folder(name)
    if api and api.path:
        return api
    env = os.environ.get(name)
    if env:
        path = _normalize_windows_path(env)
        return ResolvedPath(name, path, "environment", _existing(path))
    fallback = _fallback_path(name)
    if fallback:
        path = _normalize_windows_path(fallback)
        return ResolvedPath(name, path, "fallback", _existing(path))
    return ResolvedPath(name, "", "unresolved", False)


def _fallback_path(name: str) -> str | None:
    system_drive = os.environ.get("SystemDrive") or "C:"
    profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    if profile and profile != "~":
        profile = _normalize_windows_path(profile)
    if name == "USERPROFILE" and profile and profile != "~":
        return profile
    if name == "APPDATA" and profile and profile != "~":
        return str(PureWindowsPath(profile) / "AppData" / "Roaming")
    if name == "LOCALAPPDATA" and profile and profile != "~":
        return str(PureWindowsPath(profile) / "AppData" / "Local")
    if name == "ProgramFiles":
        return f"{system_drive}\\Program Files"
    if name == "ProgramFiles(x86)":
        return f"{system_drive}\\Program Files (x86)"
    if name == "TEMP" and profile and profile != "~":
        return str(PureWindowsPath(profile) / "AppData" / "Local" / "Temp")
    return None


def resolve_windows_environment() -> dict[str, dict[str, Any]]:
    names = ["USERPROFILE", "LOCALAPPDATA", "APPDATA", "TEMP", "ProgramFiles", "ProgramFiles(x86)"]
    return {name: resolve_known_path(name).as_dict() for name in names}


def foundry_subprocess_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Return env safe for Windows Unreal subprocesses from any shell wrapper."""
    env = dict(base or os.environ)
    for name, resolved in resolve_windows_environment().items():
        if resolved["path"]:
            env[name] = resolved["path"]
    # Prevent MSYS from rewriting Unreal args like /Game/... or C:/... when a
    # Git Bash-launched process eventually shells through .bat wrappers.
    env.setdefault("MSYS2_ARG_CONV_EXCL", "*")
    env.setdefault("MSYS_NO_PATHCONV", "1")
    return env


def git_bash_to_windows(path: str) -> str:
    text = str(path).strip()
    match = re.match(r"^/([A-Za-z])/(.*)$", text)
    if match:
        rest = match.group(2).replace("/", "\\")
        return f"{match.group(1).upper()}:\\{rest}"
    match = re.match(r"^/mnt/([A-Za-z])/(.*)$", text)
    if match:
        rest = match.group(2).replace("/", "\\")
        return f"{match.group(1).upper()}:\\{rest}"
    return text


def windows_to_git_bash(path: str | os.PathLike[str]) -> str:
    text = _normalize_windows_path(path)
    match = re.match(r"^([A-Za-z]):\\?(.*)$", text)
    if match:
        rest = match.group(2).replace("\\", "/")
        return f"/{match.group(1).lower()}/{rest}".rstrip("/")
    return text.replace("\\", "/")


def unreal_arg_path(path: str | os.PathLike[str]) -> str:
    """Absolute Windows filesystem path syntax Unreal accepts without MSYS help."""
    return _normalize_windows_path(path).replace("\\", "/")


def filesystem_path(path: str | os.PathLike[str]) -> Path:
    return Path(_normalize_windows_path(path))


def normalize_unreal_package_path(path: str) -> str:
    text = str(path).strip().replace("\\", "/")
    if not text:
        return text
    if re.match(r"^[A-Za-z]:/", text) or text.startswith("/") and not text.startswith("/Game/"):
        return text
    if not text.startswith("/Game/"):
        text = "/Game/" + text.removeprefix("Game/").lstrip("/")
    return re.sub(r"/+", "/", text)


def path_report(path: str | os.PathLike[str]) -> dict[str, str]:
    win = _normalize_windows_path(path)
    return {
        "windows_path": win,
        "posix_git_bash_path": windows_to_git_bash(win),
        "unreal_filesystem_arg": unreal_arg_path(win),
        "filesystem_path": str(Path(win)),
    }
