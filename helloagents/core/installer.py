"""HelloAGENTS Installer - Install operations."""

import json
import re
import shutil
import subprocess
from pathlib import Path

from .._common import (
    _msg,
    CLI_TARGETS, PLUGIN_DIR_NAME, AGENT_PREFIX,
    GLOBAL_CONFIG_DIR, GLOBAL_CONFIG_FILE, VALID_CONFIG_KEYS,
    is_helloagents_file, is_helloagents_rule, backup_user_file,
    get_agents_md_path, get_skill_md_path, get_helloagents_module_path,
    detect_installed_clis, clean_skills_dir, cli_dir_for,
)
from .codex_config import (
    _configure_codex_toml, _configure_codex_csv_batch,
    _configure_codex_notify,
    _configure_codex_tui_notification,
    _configure_codex_developer_instructions,
    _cleanup_codex_agents_dotted,
)
from .codex_roles import _configure_codex_agent_roles
from .claude_config import (
    _configure_claude_hooks,
    _configure_claude_permissions,
    _configure_claude_auto_memory,
)
from .claude_rules import _deploy_claude_rules
from .settings_hooks import (
    _configure_gemini_hooks, _configure_qwen_hooks, _configure_grok_hooks,
)
from .win_helpers import _is_link_or_reparse, win_safe_rmtree


# ---------------------------------------------------------------------------
# Agent definition files (Claude Code only)
# ---------------------------------------------------------------------------



def _deploy_agent_files(dest_dir: Path) -> bool:
    """Deploy HelloAGENTS agent definition files to ~/.claude/agents/."""
    agents_src = get_helloagents_module_path() / "agents"
    if not agents_src.exists():
        return True
    agents_dest = dest_dir / "agents"
    if _is_link_or_reparse(agents_dest):
        print(_msg("  ✗ agents 目录是符号链接，拒绝部署。",
                   "  ✗ Refusing to deploy into a symlinked agents directory."))
        return False
    agents_dest.mkdir(parents=True, exist_ok=True)
    source_files = list(agents_src.glob(f"{AGENT_PREFIX}*.md"))
    for src_file in source_files:
        target = agents_dest / src_file.name
        if (_is_link_or_reparse(target)
                or (target.exists() and target.read_bytes() != src_file.read_bytes())):
            print(_msg(f"  ✗ 保留同名用户 agent: {target}",
                       f"  ✗ Preserving conflicting user agent: {target}"))
            return False

    count = 0
    for src_file in source_files:
        target = agents_dest / src_file.name
        shutil.copy2(src_file, target)
        count += 1
    if count:
        print(_msg(f"  已部署 {count} 个子代理定义 ({agents_dest})",
                   f"  Deployed {count} agent definition(s) ({agents_dest})"))
    return True


# ---------------------------------------------------------------------------
# File cleanup
# ---------------------------------------------------------------------------

def clean_stale_files(dest_dir: Path, current_rules_file: str) -> list[str]:
    """Remove stale files from previous HelloAGENTS versions.

    Handles both current-version stale files and legacy (pre-v2.2) remnants.
    Only removes files confirmed to be HelloAGENTS-related.

    Args:
        dest_dir: CLI config directory (e.g. ~/.claude/).
        current_rules_file: Rules file name for this CLI target.

    Returns:
        List of removed file/directory paths.
    """
    removed = []

    # --- Clean skills/helloagents/ directory (will be re-deployed fresh if needed) ---
    try:
        removed.extend(clean_skills_dir(dest_dir))
    except Exception:
        pass

    # --- Current-version stale rules files ---
    # Only removes files confirmed to be HelloAGENTS-related (is_helloagents_file check).
    # User-created files with the same name but without HELLOAGENTS_MARKER are never touched.
    all_rules_files = {cfg["rules_file"] for cfg in CLI_TARGETS.values()}
    stale_rules = all_rules_files - {current_rules_file}
    for name in stale_rules:
        stale_path = dest_dir / name
        if stale_path.exists() and stale_path.is_file():
            if is_helloagents_file(stale_path):
                try:
                    stale_path.unlink()
                    removed.append(str(stale_path))
                except Exception:
                    pass

    # --- __pycache__ under helloagents plugin dir ---
    plugin_dir = dest_dir / PLUGIN_DIR_NAME
    if plugin_dir.exists():
        for cache_dir in plugin_dir.rglob("__pycache__"):
            if cache_dir.is_dir():
                if win_safe_rmtree(cache_dir, plugin_dir):
                    removed.append(str(cache_dir))

    # --- Clean stale rules/helloagents/ split rule files ---
    rules_ha_dir = dest_dir / "rules" / "helloagents"
    if rules_ha_dir.exists():
        for f in rules_ha_dir.glob("*.md"):
            if is_helloagents_rule(f):
                try:
                    f.unlink()
                    removed.append(f"{f} (stale rule)")
                except Exception:
                    pass
        try:
            if rules_ha_dir.exists() and not any(rules_ha_dir.iterdir()):
                rules_ha_dir.rmdir()
                removed.append(f"{rules_ha_dir} (empty)")
        except Exception:
            pass

    # --- Clean dotted agents.xxx keys in config.toml (Codex) ---
    config_toml = dest_dir / "config.toml"
    if config_toml.exists():
        try:
            content = config_toml.read_text(encoding="utf-8")
            cleaned, did_clean = _cleanup_codex_agents_dotted(content)
            if did_clean:
                config_toml.write_text(cleaned, encoding="utf-8")
                removed.append("config.toml dotted agents.xxx keys (migrated to [agents])")
        except Exception:
            pass

    return removed


# ---------------------------------------------------------------------------
# Global config creation
# ---------------------------------------------------------------------------

def _looks_like_old_default_config(data: dict) -> bool:
    """Return whether a config still matches the old generated defaults."""
    for key, default in VALID_CONFIG_KEYS.items():
        if key == "NOTIFY_LEVEL":
            continue
        if data.get(key) != default:
            return False
    return data.get("NOTIFY_LEVEL") == 0


def _sync_global_config() -> None:
    """Sync ~/.helloagents/helloagents.json with VALID_CONFIG_KEYS.

    - File missing → create with all defaults.
    - File exists  → add missing keys (defaults), warn unknown keys, preserve
      user-set values.  Only writes back when something changed.
    """
    try:
        GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(_msg(f"  ⚠ 创建全局配置目录失败: {e}",
                   f"  ⚠ Failed to create global config directory: {e}"))
        return

    if not GLOBAL_CONFIG_FILE.is_file():
        # --- brand-new file ---
        try:
            GLOBAL_CONFIG_FILE.write_text(
                json.dumps(VALID_CONFIG_KEYS, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(_msg(f"  已创建全局配置: {GLOBAL_CONFIG_FILE}",
                       f"  Created global config: {GLOBAL_CONFIG_FILE}"))
        except Exception as e:
            print(_msg(f"  ⚠ 创建全局配置失败: {e}",
                       f"  ⚠ Failed to create global config: {e}"))
        return

    # --- existing file: read → patch → write back ---
    try:
        raw = GLOBAL_CONFIG_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        print(_msg(f"  ⚠ 读取全局配置失败: {e}",
                   f"  ⚠ Failed to read global config: {e}"))
        return

    changed = False

    # Migrate legacy aliases before adding defaults. A legacy notify_level key
    # is treated as user-set and preserved.
    legacy_notify = "notify_level" in data
    if legacy_notify and "NOTIFY_LEVEL" not in data:
        data["NOTIFY_LEVEL"] = data.pop("notify_level")
        changed = True
    elif legacy_notify:
        del data["notify_level"]
        changed = True

    # Add missing keys with defaults
    added: list[str] = []
    for key, default in VALID_CONFIG_KEYS.items():
        if key not in data:
            data[key] = default
            added.append(key)
            changed = True
    if added:
        print(_msg(f"  已补充缺失配置项: {', '.join(added)}",
                   f"  Added missing config keys: {', '.join(added)}"))

    # v2.4.1+: sound notification is the default. Upgrade only untouched old
    # generated configs; legacy notify_level remains a user preference.
    if not legacy_notify and _looks_like_old_default_config(data):
        data["NOTIFY_LEVEL"] = VALID_CONFIG_KEYS["NOTIFY_LEVEL"]
        changed = True
        print(_msg("  已将默认通知模式迁移为声音通知 (NOTIFY_LEVEL=2)",
                   "  Migrated default notifications to sound (NOTIFY_LEVEL=2)"))

    # Warn about unknown keys
    unknown = [k for k in data if k not in VALID_CONFIG_KEYS]
    if unknown:
        print(_msg(f"  ⚠ 未知配置项（可能已废弃或拼写错误）: {', '.join(unknown)}",
                   f"  ⚠ Unknown config keys (possibly deprecated or misspelled): {', '.join(unknown)}"))

    if changed:
        try:
            GLOBAL_CONFIG_FILE.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception as e:
            print(_msg(f"  ⚠ 写回全局配置失败: {e}",
                       f"  ⚠ Failed to write global config: {e}"))


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def _reapply_fastctx() -> None:
    """Re-apply FastCtx integration to Codex after install rewrote its files.

    helloagents install overwrites ~/.codex/AGENTS.md (and touches config.toml),
    which removes the guidance block FastCtx manages there. Re-running
    `fastctx apply` restores the integration without user interaction.
    """
    exe = shutil.which("fastctx")
    if exe is None:
        print(_msg("  跳过 FastCtx 重新接入: 未找到 fastctx 命令（npm install -g fastctx）",
                   "  Skipped FastCtx re-apply: fastctx command not found (npm install -g fastctx)"))
        return

    tier = "standard"
    fastctx_config = Path.home() / ".fastctx" / "config.toml"
    if fastctx_config.exists():
        m = re.search(r'^\s*tier\s*=\s*"([^"]+)"',
                      fastctx_config.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            tier = m.group(1)

    try:
        result = subprocess.run(
            [exe, "apply", "--tier", tier, "--yes"],
            capture_output=True, encoding="utf-8", errors="replace", timeout=180,
        )
    except Exception as e:
        print(_msg(f"  ⚠ FastCtx 重新接入失败: {e}",
                   f"  ⚠ FastCtx re-apply failed: {e}"))
        return

    if result.returncode == 0:
        print(_msg(f"  ✅ 已重新接入 FastCtx (tier={tier})，Codex 集成已恢复",
                   f"  ✅ Re-applied FastCtx (tier={tier}); Codex integration restored"))
    else:
        detail = (result.stderr or result.stdout).strip().splitlines()
        print(_msg(f"  ⚠ FastCtx 重新接入未完成 (exit {result.returncode})",
                   f"  ⚠ FastCtx re-apply incomplete (exit {result.returncode})"))
        if detail:
            print(f"    {detail[-1]}")


def install(target: str) -> bool:
    """Install HelloAGENTS to a specific CLI."""
    if target not in CLI_TARGETS:
        print(_msg(f"  未知目标: {target}", f"  Unknown target: {target}"))
        print(_msg(f"  可用目标: {', '.join(CLI_TARGETS.keys())}",
                   f"  Available targets: {', '.join(CLI_TARGETS.keys())}"))
        return False

    config = CLI_TARGETS[target]
    dest_dir = cli_dir_for(target)
    rules_file = config["rules_file"]
    target_status = config.get("status", "active")

    if target_status == "experimental":
        print(_msg(f"  ℹ️ 提示: {target} 为实验性/社区项目，hooks 能力未经完整验证。",
                   f"  ℹ️ Note: {target} is experimental/community. Hook capabilities are not fully verified."))

    # ── Preset-mode target (DSH) ──
    if config.get("mode") == "preset":
        from .dsh_config import _install_dsh
        print(_msg(f"  正在安装 HelloAGENTS 到 {target}...",
                   f"  Installing HelloAGENTS to {target}..."))
        ok = _install_dsh(dest_dir)
        if ok:
            _sync_global_config()
        return ok

    if not dest_dir.exists():
        print(_msg(f"  警告: {dest_dir} 不存在，{target} CLI 可能未安装。",
                   f"  Warning: {dest_dir} does not exist. {target} CLI may not be installed."))
    dest_dir.mkdir(parents=True, exist_ok=True)

    agents_md_src = get_agents_md_path()
    module_src = get_helloagents_module_path()
    plugin_dest = dest_dir / PLUGIN_DIR_NAME
    rules_dest = dest_dir / rules_file

    print(_msg(f"  正在安装 HelloAGENTS 到 {target}...",
               f"  Installing HelloAGENTS to {target}..."))
    print(_msg(f"  目标目录: {dest_dir}", f"  Target directory: {dest_dir}"))

    # Clean stale files
    removed = clean_stale_files(dest_dir, rules_file)
    if removed:
        print(_msg(f"  清理了 {len(removed)} 个过期文件:",
                   f"  Cleaned {len(removed)} stale file(s):"))
        for r in removed:
            print(f"    - {r}")

    try:
        # Remove old module directory completely before copying
        if plugin_dest.exists():
            if not win_safe_rmtree(plugin_dest, dest_dir):
                print(_msg(f"  ✗ 无法移除旧模块（可能被 CLI 进程占用）: {plugin_dest}",
                           f"  ✗ Cannot remove old module (may be locked by CLI): {plugin_dest}"))
                return False
            print(_msg(f"  已移除旧模块: {plugin_dest}",
                       f"  Removed old module: {plugin_dest}"))

        # Copy new module directory
        shutil.copytree(
            module_src, plugin_dest,
            ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", "hooks", "agents",
                "core",         # CLI management modules (not needed at deploy target)
                "cli.py", "__main__.py",  # CLI entry points
            ),
        )
        print(_msg(f"  已安装模块到: {plugin_dest}",
                   f"  Installed module to: {plugin_dest}"))

        # Deploy rules
        if agents_md_src.exists():
            if target == "claude":
                # Split deployment for Claude Code (avoid 40k char warning)
                if rules_dest.exists() and not is_helloagents_file(rules_dest):
                    backup = backup_user_file(rules_dest)
                    print(_msg(f"  已备份现有规则到: {backup}",
                               f"  Backed up existing rules to: {backup}"))
                count = _deploy_claude_rules(dest_dir, agents_md_src)
                print(_msg(f"  已部署拆分规则: {count} 个文件 (CLAUDE.md + rules/helloagents/)",
                           f"  Deployed split rules: {count} file(s) (CLAUDE.md + rules/helloagents/)"))
            else:
                # Full deployment for non-Claude CLIs (direct copy of AGENTS.md)
                # Non-Claude CLIs lack native rules/ auto-loading; split deployment
                # would rely on AI following bootstrap instructions, which is unreliable.
                if rules_dest.exists() and not is_helloagents_file(rules_dest):
                    backup = backup_user_file(rules_dest)
                    print(_msg(f"  已备份现有规则到: {backup}",
                               f"  Backed up existing rules to: {backup}"))
                is_update = rules_dest.exists()
                shutil.copy2(agents_md_src, rules_dest)
                if is_update:
                    print(_msg(f"  已更新规则: {rules_dest}",
                               f"  Updated rules: {rules_dest}"))
                else:
                    print(_msg(f"  已安装规则: {rules_dest}",
                               f"  Installed rules: {rules_dest}"))
        else:
            print(_msg(f"  警告: 未找到 AGENTS.md ({agents_md_src})",
                       f"  Warning: AGENTS.md not found at {agents_md_src}"))

        # Deploy SKILL.md to skills discovery directory
        skill_md_src = get_skill_md_path()
        if skill_md_src.exists():
            skill_dest_dir = dest_dir / "skills" / "helloagents"
            skill_dest = skill_dest_dir / "SKILL.md"
            skill_dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill_md_src, skill_dest)
            print(_msg(f"  已部署技能: {skill_dest}",
                       f"  Deployed skill: {skill_dest}"))

        # Deploy agent definition files (Claude Code only)
        if target == "claude":
            if not _deploy_agent_files(dest_dir):
                return False
    except Exception as e:
        print(_msg(f"  ✗ 安装失败: {e}", f"  ✗ Installation failed: {e}"))
        return False

    # 同步全局配置文件（补缺失键、警告未知键）
    _sync_global_config()

    if GLOBAL_CONFIG_FILE.exists():
        print(_msg(f"  ℹ 个性化配置: {GLOBAL_CONFIG_FILE}",
                   f"  ℹ Custom settings: {GLOBAL_CONFIG_FILE}"))
    else:
        print(_msg("  ℹ 个性化配置可写入 ~/.helloagents/helloagents.json，更新时不会被覆盖。",
                   "  ℹ Custom settings can be saved to ~/.helloagents/helloagents.json (preserved across updates)."))

    # Target-specific post-install: hooks & config
    _POST_INSTALL = {
        "claude": [
            (_configure_claude_hooks,       "Hooks",       "Hooks"),
            (_configure_claude_permissions, "工具权限",    "tool permissions"),
            (_configure_claude_auto_memory, "autoMemory",  "autoMemory"),
        ],
        "codex": [
            (_configure_codex_toml,                   "config.toml",              "config.toml"),
            (_configure_codex_notify,                 "notify hook",              "notify hook"),
            (_configure_codex_tui_notification,       "TUI 通知方式",            "TUI notification"),
            (_configure_codex_csv_batch,              "CSV 批处理",              "CSV batch"),
            (_configure_codex_agent_roles,            "子代理角色",              "agent roles"),
            (_configure_codex_developer_instructions, "developer_instructions",   "developer_instructions"),
        ],
        "gemini": [
            (_configure_gemini_hooks, "Hooks", "Hooks"),
        ],
        "qwen": [
            (_configure_qwen_hooks, "Hooks", "Hooks"),
        ],
        "grok": [
            (_configure_grok_hooks, "Hooks", "Hooks"),
        ],
        # opencode: 纯规则模式，无 hooks/settings.json 配置
    }
    post_install_ok = True
    for fn, cn_label, en_label in _POST_INSTALL.get(target, []):
        try:
            if fn(dest_dir) is False:
                post_install_ok = False
                print(_msg(f"  ✗ 配置 {cn_label} 失败",
                           f"  ✗ Failed to configure {en_label}"))
        except Exception as e:
            post_install_ok = False
            print(_msg(f"  ⚠ 配置 {cn_label} 时出错: {e}",
                       f"  ⚠ Error configuring {en_label}: {e}"))

    if not post_install_ok:
        print(_msg(f"  ✗ {target} 安装未完整完成。",
                   f"  ✗ Installation for {target} did not complete."))
        return False

    print(_msg(f"  {target} 安装完成！请重启终端以应用更改。",
               f"  Installation complete for {target}! Please restart your terminal to apply changes."))

    if target == "codex":
        print(_msg("  提示: 需在 Codex CLI 中执行 /experimental 开启多代理功能。",
                   "  Note: Run /experimental in Codex CLI to enable multi-agent features."))
        print(_msg("  提示: VS Code Codex 插件对 HelloAGENTS 系统的支持可能与 CLI 不同，建议优先在 Codex CLI 中使用。",
                   "  Note: VS Code Codex plugin may not fully support HelloAGENTS. Codex CLI is recommended."))
        # install 会覆盖 ~/.codex/AGENTS.md，移除 FastCtx 管理的指引块；
        # 立即重新接入 FastCtx，防止丢失其配置。
        _reapply_fastctx()

    return True


def install_all() -> bool:
    """Install to all detected CLI directories."""
    detected = detect_installed_clis()
    if not detected:
        print(_msg("  未检测到 CLI 目录。", "  No CLI directories detected."))
        print(_msg(f"  支持的 CLI: {', '.join(CLI_TARGETS.keys())}",
                   f"  Supported CLIs: {', '.join(CLI_TARGETS.keys())}"))
        return False

    print(_msg(f"  检测到的 CLI: {', '.join(detected)}",
               f"  Detected CLIs: {', '.join(detected)}"))
    failed = []
    for target in detected:
        if not install(target):
            failed.append(target)
        print()

    if failed:
        print(_msg(f"  失败: {', '.join(failed)}", f"  Failed: {', '.join(failed)}"))
        return False
    return True
