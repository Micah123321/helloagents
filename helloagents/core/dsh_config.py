"""HelloAGENTS DSH (DeepSeek Harness) target — install/uninstall/status.

This module is the DSH-specific config writer, mirroring the role of
``claude_config.py`` / ``codex_config.py`` for other targets.  DSH uses a
fundamentally different plugin model (agent presets instead of hook files),
so the generic ``install()``/``uninstall()``/``status()`` code branches to
this module when ``CLI_TARGETS[name]["mode"] == "preset"``.
"""

import os
import shutil
from pathlib import Path
from importlib.resources import files as _package_files

from .._common import (
    _msg,
    PLUGIN_DIR_NAME,
    HELLOAGENTS_MARKER,
    get_skill_md_path,
)

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_tick = "\u2713"   # ✓
_cross = "\u2717"  # ✗

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DSH_HOME_ENV = "DSH_HOME"
_AGENT_PRESET_DIR = ".agent-presets"
_PRESET_ID = PLUGIN_DIR_NAME  # "helloagents"

# Files shipped in the package under helloagents/dsh/
_TEMPLATE_PREFIX = "dsh"
_TEMPLATE_FILES = (
    "agent.cordis.yml",
    "preset.yml",
    "bootstrap.md",
    "helloagents-carrier.mjs",
    # skills/helloagents/SKILL.md is copied from get_skill_md_path() at runtime
)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _dsh_home() -> Path:
    """Return the DSH home directory ($DSH_HOME or ~/.dsh)."""
    env = os.environ.get(_DSH_HOME_ENV)
    if env and env.strip():
        return Path(env.strip())
    return Path.home() / ".dsh"


def _preset_dir(dsh_home: Path | None = None) -> Path:
    """Return the agent preset directory for HelloAGENTS under DSH."""
    if dsh_home is None:
        dsh_home = _dsh_home()
    return dsh_home / _AGENT_PRESET_DIR / _PRESET_ID


def _template_dir() -> Path:
    """Return the package-local template directory (helloagents/dsh/)."""
    return Path(str(_package_files("helloagents"))) / _TEMPLATE_PREFIX


# ---------------------------------------------------------------------------
# Marker check
# ---------------------------------------------------------------------------

def _is_managed(preset_dir: Path) -> bool:
    """Return whether ``preset_dir/agent.cordis.yml`` carries our marker."""
    agent_yml = preset_dir / "agent.cordis.yml"
    if not agent_yml.is_file():
        return False
    try:
        head = agent_yml.read_bytes()[:1024]
        return HELLOAGENTS_MARKER.encode("utf-8") in head
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def _install_dsh(dsh_home: Path) -> bool:
    """Install (or refresh) the HelloAGENTS agent preset under *dsh_home*.

    Returns ``True`` on success, ``False`` if any file operation failed.
    """
    preset_dir = _preset_dir(dsh_home)
    skills_dir = preset_dir / "skills" / "helloagents"
    template_dir = _template_dir()

    try:
        # ● Backup existing preset if it is not ours
        if preset_dir.exists() and not _is_managed(preset_dir):
            backup = preset_dir.with_suffix(".bak")
            if backup.exists():
                shutil.rmtree(backup)
            preset_dir.rename(backup)
            print(_msg(
                f"  … 备份已有 preset: {preset_dir} → {backup}",
                f"  … Backed up existing preset: {preset_dir} → {backup}",
            ))

        # ● Create directory structure
        preset_dir.mkdir(parents=True, exist_ok=True)
        (preset_dir / "plugins").mkdir(parents=True, exist_ok=True)
        skills_dir.mkdir(parents=True, exist_ok=True)

        # ● Copy template files
        for name in _TEMPLATE_FILES:
            src = template_dir / name
            if name == "helloagents-carrier.mjs":
                dst = preset_dir / "plugins" / name
            else:
                dst = preset_dir / name
            if not src.is_file():
                print(_msg(f"  ✗ 模板文件缺失: {name}", f"  ✗ Missing template: {name}"))
                return False
            shutil.copy2(src, dst)

        # ● Copy SKILL.md (from the package root)
        skill_src = get_skill_md_path()
        if skill_src and skill_src.is_file():
            skill_dst = skills_dir / "SKILL.md"
            shutil.copy2(skill_src, skill_dst)
        else:
            print(_msg(
                "  ⚠ 未找到 SKILL.md（技能文件仍位于安装副本）",
                "  ⚠ SKILL.md not found; skill remains in the module copy",
            ))

        print(_msg(
            f"  ✓ DSH agent preset 已安装: {preset_dir}",
            f"  ✓ DSH agent preset installed: {preset_dir}",
        ))
        return True

    except OSError as exc:
        print(_msg(
            f"  ✗ 安装失败: {exc}",
            f"  ✗ Install failed: {exc}",
        ))
        return False


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def _uninstall_dsh(dsh_home: Path) -> list[str]:
    """Remove the HelloAGENTS agent preset under *dsh_home*.

    Only removes the preset directory if it carries our marker.  Returns the
    list of removed paths (empty when nothing was removed).
    """
    preset_dir = _preset_dir(dsh_home)
    if not preset_dir.exists():
        print(_msg(
            "  DSH preset 目录不存在，跳过卸载。",
            "  DSH preset directory does not exist; skipping uninstall.",
        ))
        return []

    if not _is_managed(preset_dir):
        print(_msg(
            f"  ⚠ DSH preset 目录 {preset_dir} 不属于 HelloAGENTS，"
            f"已跳过（保留用户数据）。",
            f"  ⚠ DSH preset directory {preset_dir} is not managed by "
            f"HelloAGENTS; preserved (user data).",
        ))
        return []

    removed = []
    try:
        for item in preset_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            removed.append(str(item))
        preset_dir.rmdir()
        removed.append(str(preset_dir))
        print(_msg(
            f"  ✓ DSH agent preset 已卸载: {preset_dir}",
            f"  ✓ DSH agent preset uninstalled: {preset_dir}",
        ))
    except OSError as exc:
        print(_msg(
            f"  ✗ 卸载失败: {exc}",
            f"  ✗ Uninstall failed: {exc}",
        ))

    return removed


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def _show_dsh_details(dsh_home: Path) -> dict[str, bool]:
    """Show the status of the HelloAGENTS DSH preset and return a detail map.

    Keys in the returned dict:
        preset_dir    — whether the preset directory exists
        composition   — agent.cordis.yml exists and has content
        bootstrap     — bootstrap.md exists and is non-empty
        carrier       — plugins/helloagents-carrier.mjs exists
        metadata      — preset.yml exists
        skill         — skills/helloagents/SKILL.md exists
    """
    preset_dir = _preset_dir(dsh_home)
    details: dict[str, bool] = {}

    # Basic presence
    details["preset_dir"] = preset_dir.is_dir()

    if not details["preset_dir"]:
        for k in ("composition", "bootstrap", "carrier", "metadata", "skill"):
            details[k] = False
        return details

    # File-level checks
    details["composition"] = _min_size(preset_dir / "agent.cordis.yml", 10)
    details["bootstrap"] = _min_size(preset_dir / "bootstrap.md", 10)
    details["carrier"] = (preset_dir / "plugins" / "helloagents-carrier.mjs").is_file()
    details["metadata"] = (preset_dir / "preset.yml").is_file()
    details["skill"] = _min_size(preset_dir / "skills" / "helloagents" / "SKILL.md", 10)

    # Print summary
    checks = [
        ("composition", "组合文件", "Composition"),
        ("bootstrap", "DSH 适配协议", "DSH-adapted protocol"),
        ("carrier", "carrier 插件", "Carrier plugin"),
        ("metadata", "元数据", "Metadata"),
        ("skill", "技能文件", "Skill"),
    ]
    for key, zh, en in checks:
        ok = details.get(key, False)
        icon = _tick if ok else _cross
        status = _msg("正常", "OK") if ok else _msg("缺失", "missing")
        print(f"    {icon} {zh}/{en}: {status}")

    print()
    path = _preset_dir(dsh_home)
    print(_msg(
        f"  DSH 会话中请选择预设「HelloAGENTS 模式」来启用工作流。",
        f"  Select the 'HelloAGENTS 模式' preset in DSH to activate the workflow.",
    ))
    print(_msg(
        f"  DSH preset 路径: {path}",
        f"  DSH preset path: {path}",
    ))

    return details


def _min_size(path: Path, minimum: int) -> bool:
    """Return whether *path* exists and its size is >= *minimum* bytes."""
    try:
        return path.is_file() and path.stat().st_size >= minimum
    except OSError:
        return False