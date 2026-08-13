"""HelloAGENTS Updater - Update command and post-update sync."""

import os
import re
import sys
from urllib.parse import urlsplit
from importlib.metadata import version as get_version

from .._common import (
    _msg, _header,
    REPO_URL,
    _detect_installed_targets, _detect_install_method,
)
from .version_check import (
    _detect_channel, _local_commit_id, _remote_commit_id,
    _get_repo_url, _version_newer, _write_update_cache, fetch_latest_version,
    _resolve_branch,
)
from .win_helpers import (
    _cleanup_pip_remnants, _win_cleanup_bak,
    _win_deferred_pip, build_pip_cleanup_cmd,
    win_preemptive_unlock, win_finish_unlock,
)


# ---------------------------------------------------------------------------
# update command
# ---------------------------------------------------------------------------

def _build_git_install_url(repo_url: str, commit: str) -> str:
    """Build a pip/uv VCS URL pinned to a verified commit."""
    base = (repo_url or REPO_URL).removeprefix("git+")
    if base.startswith("https://github.com/") and not base.endswith(".git"):
        base = f"{base}.git"
    return f"git+{base}@{commit}"


def _is_safe_update_source(repo_url: str) -> bool:
    """Allow only the canonical credential-free HTTPS repository."""
    parsed = urlsplit(repo_url.removeprefix("git+"))
    parts = [part for part in parsed.path.split("/") if part]
    return (
        parsed.scheme == "https"
        and parsed.hostname == "github.com"
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and len(parts) == 2
        and parts[0].lower() == "micah123321"
        and parts[1].removesuffix(".git").lower() == "helloagents"
    )


def _is_windows_entrypoint_lock_error(text: str) -> bool:
    """Return whether uv/pip failed while the running helloagents.exe is locked.

    Two failure shapes are recognized:
    1. Entry-point lock: uv could not copy/replace ``helloagents.exe``
       (``failed to install entrypoint`` / ``helloagents.exe`` + in-use marker).
    2. Tool-env directory lock: uv could not remove the uv tool env directory
       (``failed to remove directory ...\\Scripts`` / ``os error 5``) because the
       running ``helloagents.exe`` lives inside it and Windows holds the file lock.

    Both stem from the same root cause: the user runs ``helloagents`` from a
    shell whose current process is the very entry point being replaced.
    """
    if not text:
        return False

    lower = text.lower()
    entrypoint_markers = (
        "failed to install entrypoint",
        "helloagents.exe",
        "failed to remove directory",  # uv tool-env directory lock
    )
    lock_markers = (
        "os error 5",
        "os error 32",
        "winerror 32",
        "winerror 5",
        "being used by another process",
        "used by another process",
        "access is denied",          # Windows ACL denial during tool-env removal
        "permission denied",
        "另一个程序正在使用此文件",
        "拒绝访问",                  # Chinese: access denied
        "进程无法访问",
    )
    return (
        any(marker in lower for marker in entrypoint_markers)
        and any(marker in lower for marker in lock_markers)
    )


def _uv_toolenv_lock_error(text: str) -> bool:
    """Return whether uv failed specifically on the tool-env directory removal.

    uv's tool-env lock surfaces as:
      ``error: failed to remove directory `...\\helloagents\\Scripts`: ... (os error 5)``
    which the running helloagents.exe blocks. This is a stricter, more reliable
    signal than the generic entrypoint check because the directory path is stable.
    """
    if not text:
        return False
    lower = text.lower()
    return (
        "failed to remove directory" in lower
        and ("scripts" in lower or "helloagents" in lower)
        and ("os error 5" in lower or "os error 32" in lower
             or "access is denied" in lower or "permission denied" in lower
             or "拒绝访问" in lower)
    )


def _attempt_deferred_reinstall(install_cmd: list[str], branch: str,
                                total_steps: int, pre_targets: list[str],
                                bak) -> bool:
    """Schedule install_cmd to run after this process exits (Windows lock).

    Used as the fallback when uv/pip fails mid-reinstall because the running
    helloagents.exe locks files. Returns True if deferred install scheduled.
    The deferred runner completes the reinstall after the shell exits, so the
    package never ends up in a broken half-installed state.
    """
    if sys.platform != "win32":
        return False
    post = [[sys.executable, "-m", "helloagents.cli",
             "_post_update", branch, str(total_steps)]]
    all_post = post + [build_pip_cleanup_cmd()]
    if _win_deferred_pip(install_cmd, post_cmds=all_post):
        print(_msg(
            "  helloagents.exe 被当前会话锁定，"
            "更新将在退出后自动完成。",
            "  helloagents.exe is locked by the current session; "
            "update will complete automatically after exit."))
        if pre_targets:
            print(_msg(
                f"  已安装的 {len(pre_targets)} 个 CLI "
                f"工具也将自动同步。",
                f"  {len(pre_targets)} installed target(s) "
                f"will also be synced."))
        win_finish_unlock(bak, False)
        return True
    return False


def update(switch_branch: str | None = None) -> None:
    """Update HelloAGENTS to the latest version, then auto-sync installed targets."""
    import subprocess

    # Snapshot installed targets before update. In deferred mode (Windows exe lock),
    # these targets are passed as post_cmds to the deferred script. The slight timing
    # gap is acceptable — users won't modify install state during an active update.
    pre_targets = _detect_installed_targets()
    total_steps = 3 if pre_targets else 1

    # ── Phase 1: Update package ──
    _header(_msg(f"步骤 1/{total_steps}: 更新 HelloAGENTS 包",
                 f"Step 1/{total_steps}: Update HelloAGENTS Package"))

    local_ver = "unknown"
    try:
        local_ver = get_version("helloagents")
    except Exception:
        pass

    branch = switch_branch or _resolve_branch(local_ver)
    repo_url = _get_repo_url()
    if not _is_safe_update_source(repo_url):
        print(_msg(
            f"  ✗ 拒绝不受支持的更新来源: {repo_url}",
            f"  ✗ Refusing unsupported update source: {repo_url}"))
        return

    try:
        pinned_commit = _remote_commit_id(branch, repo_url)
    except Exception:
        pinned_commit = ""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", pinned_commit):
        print(_msg(
            "  ✗ 无法解析并验证远程 commit，已取消更新。",
            "  ✗ Could not resolve and verify the remote commit; update cancelled."))
        return

    # Fetch remote version (unified helper — deduplicates old inline logic)
    print(_msg("  正在检查远程版本...", "  Checking remote version..."))
    remote_ver = fetch_latest_version(branch, timeout=5,
                                      repo_url=repo_url,
                                      local_ver=local_ver)

    print(_msg(f"  本地版本: {local_ver}", f"  Local version: {local_ver}"))
    print(_msg(f"  远程版本: {remote_ver or '未知'}", f"  Remote version: {remote_ver or 'unknown'}"))
    print(_msg(f"  分支: {branch}", f"  Branch: {branch}"))
    print(_msg(f"  固定 commit: {pinned_commit}", f"  Pinned commit: {pinned_commit}"))
    print()

    # --- user confirmation ---
    if remote_ver and _version_newer(remote_ver, local_ver):
        prompt = _msg(
            f"  发现新版本 {remote_ver}，是否更新？(Y/n): ",
            f"  New version {remote_ver} available. Update? (Y/n): ")
        default_yes = True
    elif remote_ver and remote_ver == local_ver:
        local_sha = _local_commit_id()
        remote_sha = pinned_commit
        if local_sha and remote_sha and local_sha == remote_sha:
            prompt = _msg(
                "  本地版本与远程仓库完全一致，是否强制覆盖更新？(y/N): ",
                "  Local version matches remote. Force reinstall? (y/N): ")
            default_yes = False
        else:
            prompt = _msg(
                "  版本号相同但远程仓库可能有新提交，是否更新？(Y/n): ",
                "  Same version but remote may have new commits. Update? (Y/n): ")
            default_yes = True
    else:
        prompt = _msg(
            "  无法确认远程版本，是否继续更新？(Y/n): ",
            "  Cannot determine remote version. Continue? (Y/n): ")
        default_yes = True

    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        print(_msg("  已取消。", "  Cancelled."))
        return

    if default_yes:
        if answer in ("n", "no"):
            print(_msg("  已取消。", "  Cancelled."))
            return
    else:
        if answer not in ("y", "yes"):
            print(_msg("  已取消。", "  Cancelled."))
            return

    print()

    # Cleanup is destructive, so it runs only after explicit confirmation.
    _cleanup_pip_remnants()
    if sys.platform == "win32":
        _win_cleanup_bak()

    # --- execute update ---
    install_url = _build_git_install_url(repo_url, pinned_commit)
    updated = False
    method = _detect_install_method()
    in_venv = sys.prefix != sys.base_prefix
    print(_msg("  正在从远程仓库下载并安装，请稍候...",
               "  Downloading and installing from remote, please wait..."))

    # Preemptive unlock: rename exe BEFORE pip/uv to avoid lock entirely
    bak = win_preemptive_unlock()
    allow_pip_fallback = method != "uv"

    # Try uv first
    uv_failed_text = ""  # captured for lock detection if uv errors
    if method == "uv":
        # Inside a venv: install into the venv, not the tool environment
        if in_venv:
            uv_cmd = [
                "uv", "pip", "install", "--upgrade",
                "--force-reinstall", "--no-cache-dir", install_url,
            ]
        else:
            uv_cmd = [
                "uv", "tool", "install", "--from", install_url,
                "helloagents", "--force", "--no-cache",
            ]
        try:
            result = subprocess.run(uv_cmd, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            if result.returncode == 0:
                print(result.stdout.strip() if result.stdout.strip()
                      else _msg("  ✓ 包更新完成 (uv)", "  ✓ Package updated (uv)"))
                updated = True
            else:
                stdout = result.stdout.strip()
                stderr = result.stderr.strip()
                combined = f"{stdout}\n{stderr}"
                uv_failed_text = combined
                if not in_venv:
                    # Lock failure (entrypoint or tool-env directory) → defer to
                    # post-exit so the running exe stops blocking the reinstall.
                    # Not applicable when installing into a venv.
                    if sys.platform == "win32" and (
                            _is_windows_entrypoint_lock_error(combined)
                            or _uv_toolenv_lock_error(combined)):
                        if _attempt_deferred_reinstall(
                                uv_cmd, branch, total_steps, pre_targets, bak):
                            return
                        # deferred scheduling itself failed → fall through to pip
                        # fallback as a last resort (still tries to recover)
                if stderr:
                    print(f"  uv error: {stderr}")
                elif stdout:
                    print(f"  uv error: {stdout}")
        except FileNotFoundError:
            print(_msg("  警告: 未找到 uv，回退到 pip。",
                       "  Warning: uv not found, falling back to pip."))
            allow_pip_fallback = True

    # Fallback to pip (covers: uv not found, uv true-failure, uv non-Windows,
    # and venv mode where uv pip install failed).
    # On Windows, a uv lock failure that couldn't be deferred is retried via pip;
    # pip's own lock failure is handled by its deferred branch below.
    if not updated and (allow_pip_fallback or in_venv):
        pip_cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
                   "--no-cache-dir", install_url]
        try:
            result = subprocess.run(pip_cmd, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            if result.returncode == 0:
                print(_msg("  ✓ 包更新完成 (pip)", "  ✓ Package updated (pip)"))
                updated = True
            else:
                stderr = result.stderr.strip()
                combined = f"{result.stdout.strip()}\n{stderr}"
                # Preemptive unlock failed or not Windows — last resort deferred
                if sys.platform == "win32" and (
                        _is_windows_entrypoint_lock_error(combined)
                        or _uv_toolenv_lock_error(combined)
                        or "WinError" in combined
                        or "helloagents.exe" in combined):
                    if _attempt_deferred_reinstall(
                            pip_cmd, branch, total_steps, pre_targets, bak):
                        return
                    elif stderr:
                        print(f"  pip error: {stderr}")
                elif stderr:
                    print(f"  pip error: {stderr}")
        except FileNotFoundError:
            print(_msg("  错误: 未找到 pip。", "  Error: pip not found."))

    # Finish preemptive unlock: clean .bak on success, restore on failure
    win_finish_unlock(bak, updated)

    # Clean up pip remnants created during upgrade (pure file cleanup, safe with old code)
    _cleanup_pip_remnants()

    if not updated:
        print(_msg("  ✗ 更新失败。请手动执行:", "  ✗ Update failed. Try manually:"))
        if method == "uv" and not allow_pip_fallback:
            print(f"    uv tool install --from {install_url} helloagents --force --no-cache")
        else:
            print(f"    pip install --upgrade --no-cache-dir {install_url}")
        # Lock-failure guidance: the running helloagents.exe blocks the reinstall
        # when invoked from the project directory. Tell the user the actionable
        # fix so they're not left guessing why the manual command is needed.
        lock_hint_zh = (
            uv_failed_text and sys.platform == "win32"
            and (_is_windows_entrypoint_lock_error(uv_failed_text)
                 or _uv_toolenv_lock_error(uv_failed_text)))
        if lock_hint_zh:
            print(_msg(
                "  → 根因: helloagents.exe 被当前会话锁定。"
                "换个目录运行，或退出当前会话后再执行上述命令。",
                "  → Cause: helloagents.exe is locked by the current session. "
                "Run from a different directory or exit this session first."))
        return

    # Re-exec: launch a NEW process for Phase 2+3 so that the freshly
    # installed code on disk is what actually runs (cache write, target
    # detection, sync).  This avoids stale in-memory code after branch switch.
    env = os.environ.copy()
    env["HELLOAGENTS_NO_UPDATE_CHECK"] = "1"
    post_result = subprocess.run(
        [sys.executable, "-m", "helloagents.cli",
         "_post_update", branch, str(total_steps)],
        env=env,
    )
    if post_result.returncode != 0:
        raise RuntimeError(_msg(
            "更新包已安装，但 CLI 安全配置同步失败。",
            "Package updated, but CLI security configuration sync failed.",
        ))


# ---------------------------------------------------------------------------
# _post_update_sync – Phase 2+3 entry point (runs in new process after update)
# ---------------------------------------------------------------------------

def _post_update_sync(branch: str | None = None,
                      total_steps: int | None = None) -> bool:
    """Execute Phase 2+3 after a successful package update.

    This function is designed to be called from a *new* process so that the
    freshly-installed code on disk is what actually runs.  It covers:
      - Writing the update cache with the new version
      - Detecting currently installed targets (using new code)
      - Syncing each target via ``helloagents install``
      - Printing a summary
    """
    import subprocess

    try:
        new_ver = get_version("helloagents")
    except Exception:
        new_ver = "unknown"
    if not branch:
        branch = _detect_channel(new_ver)
    _write_update_cache(False, new_ver, new_ver, branch)

    # Detect targets using new code
    targets = _detect_installed_targets()

    # Resolve total_steps if not provided
    if total_steps is None:
        total_steps = 3 if targets else 1

    # ── Phase 2: Sync installed targets ──
    if targets:
        _header(_msg(
            f"步骤 2/{total_steps}: 同步已安装的 CLI 工具（共 {len(targets)} 个）",
            f"Step 2/{total_steps}: Syncing Installed CLI Targets ({len(targets)} target(s))"))
        results = {}
        for i, t in enumerate(targets, 1):
            print(_msg(f"  [{i}/{len(targets)}] {t}", f"  [{i}/{len(targets)}] {t}"))
            env = os.environ.copy()
            env["HELLOAGENTS_NO_UPDATE_CHECK"] = "1"
            ret = subprocess.run(
                [sys.executable, "-m", "helloagents.cli", "install", t],
                encoding="utf-8", errors="replace", env=env,
            )
            results[t] = ret.returncode == 0
            print()

        _header(_msg(f"步骤 3/{total_steps}: 更新完成",
                     f"Step 3/{total_steps}: Update Complete"))
        for t, ok in results.items():
            mark = "✓" if ok else "✗"
            status_text = (_msg("已同步", "synced") if ok
                           else _msg("同步失败", "sync failed"))
            print(f"  {mark} {t:10} {status_text}")
        print()
        return all(results.values())
    else:
        print()
        print(_msg("  未检测到已安装的 CLI 目标。执行 'helloagents' 选择安装。",
                   "  No installed CLI targets detected. Run 'helloagents' to install."))
        return True
