#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Desktop and sound notification channels for HelloAGENTS."""

from __future__ import annotations

import html
import base64
import subprocess
import sys
from pathlib import Path

from _notify_context import NotificationContext


SCRIPTS_DIR = Path(__file__).parent
SOUND_NOTIFY = SCRIPTS_DIR / "sound_notify.py"
WIN_APPID = "HelloAgents.Notification"
ICON_PATH = Path(__file__).parent.parent / "assets" / "icons" / "icon.png"


def send_desktop(title: str, message: str) -> None:
    """Send a desktop notification on the current platform."""
    if sys.platform == "win32":
        _notify_windows(title, message)
    elif sys.platform == "darwin":
        _notify_macos(title, message)
    else:
        _notify_linux(title, message)


def play_context_sound(context: NotificationContext) -> None:
    """Speak dynamic context text, falling back to the existing event WAV."""
    if _speak(context.speech):
        return
    _play_wav_event(context.event)


def bell() -> None:
    """Final fallback terminal bell."""
    print("\a", end="", file=sys.stderr, flush=True)


def _notify_windows(title: str, message: str) -> None:
    _ensure_win_appid(title)
    icon = f'<image placement="appLogoOverride" src="{ICON_PATH}" />' if ICON_PATH.is_file() else ""
    xml = (
        "<toast><visual><binding template=\"ToastGeneric\">"
        f"{icon}<text>{html.escape(title)}</text><text>{html.escape(message)}</text>"
        "</binding></visual></toast>"
    )
    ps_cmd = (
        "Add-Type -AssemblyName System.Runtime.WindowsRuntime;"
        "[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null;"
        "[Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom,ContentType=WindowsRuntime]|Out-Null;"
        f"$xml=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{_b64(xml)}'));"
        "$doc=New-Object Windows.Data.Xml.Dom.XmlDocument;"
        "$doc.LoadXml($xml);"
        "$toast=[Windows.UI.Notifications.ToastNotification]::new($doc);"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{WIN_APPID}').Show($toast)"
    )
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", _ps_encoded(ps_cmd)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        if result.returncode != 0:
            bell()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        bell()


def _ensure_win_appid(display_name: str) -> None:
    reg_key = f"HKCU:\\Software\\Classes\\AppUserModelId\\{WIN_APPID}"
    safe_name = display_name.replace("'", "''")
    ps_cmd = (
        f"if (-not (Test-Path '{reg_key}')) {{"
        f"New-Item -Path '{reg_key}' -Force | Out-Null;"
        f"Set-ItemProperty -Path '{reg_key}' -Name 'DisplayName' -Value '{safe_name}' -Force}}"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass


def _notify_macos(title: str, message: str) -> None:
    script = f'display notification "{_osa_escape(message)}" with title "{_osa_escape(title)}"'
    try:
        subprocess.run(["osascript", "-e", script],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        bell()


def _notify_linux(title: str, message: str) -> None:
    try:
        result = subprocess.run(["notify-send", title, message],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        if result.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    bell()


def _speak(text: str) -> bool:
    if sys.platform == "win32":
        return _speak_windows(text)
    if sys.platform == "darwin":
        return _spawn_audio(["say", text])
    return _spawn_audio(["spd-say", text]) or _spawn_audio(["espeak", text])


def _speak_windows(text: str) -> bool:
    ps_cmd = (
        "Add-Type -AssemblyName System.Speech;"
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$s.Speak($args[0])"
    )
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd, text],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def _spawn_audio(argv: list[str]) -> bool:
    try:
        subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (FileNotFoundError, OSError):
        return False


def _play_wav_event(event: str) -> None:
    if not SOUND_NOTIFY.exists():
        bell()
        return
    try:
        subprocess.run([sys.executable, str(SOUND_NOTIFY), event],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        bell()


def _osa_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _ps_encoded(script: str) -> str:
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")
