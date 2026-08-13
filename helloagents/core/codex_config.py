"""HelloAGENTS Codex Config - Codex CLI config.toml configuration helpers."""

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None

from .._common import _msg, CODEX_NOTIFY_SCRIPT, PLUGIN_DIR_NAME, get_python_cmd


# ---------------------------------------------------------------------------
# Shared TOML helpers
# ---------------------------------------------------------------------------

def _insert_before_first_section(content: str, line: str) -> str:
    """Insert a line before the first TOML [section] header, or at the top.

    Adds a trailing blank line if inserting mid-file (before a section).
    """
    insert_pos = 0
    section_match = re.search(r'^\[[\w]', content, re.MULTILINE)
    if section_match:
        insert_pos = section_match.start()
    text = line + "\n"
    if insert_pos > 0:
        text += "\n"
    return content[:insert_pos] + text + content[insert_pos:]


# ---------------------------------------------------------------------------
# Codex config.toml helpers
# ---------------------------------------------------------------------------

def _configure_codex_toml(dest_dir: Path) -> None:
    """Ensure config.toml has project_doc_max_bytes >= 131072."""
    config_path = dest_dir / "config.toml"
    content = ""
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")

    # Already set and large enough — nothing to do
    m = re.search(r'project_doc_max_bytes\s*=\s*(\d+)', content)
    if m and int(m.group(1)) >= 131072:
        return

    if m:
        # Exists but value is too small — replace it
        content = re.sub(
            r'project_doc_max_bytes\s*=\s*\d+',
            'project_doc_max_bytes = 131072',
            content)
    else:
        # Not present — insert before the first [section] or at the top
        content = _insert_before_first_section(
            content, "project_doc_max_bytes = 131072")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    print(_msg("  已配置 project_doc_max_bytes = 131072 (防止 AGENTS.md 被截断)",
               "  Configured project_doc_max_bytes = 131072 (prevent AGENTS.md truncation)"))


def _cleanup_codex_agents_dotted(content: str) -> tuple[str, bool]:
    """Remove legacy dotted keys before creating managed TOML sections.

    Returns (cleaned_content, was_changed).
    """
    cleaned = content
    changed = False
    dotted_keys = (
        "agents.max_threads",
        "agents.max_depth",
        "agents.interrupt_message",
        "agents.max_concurrent_threads_per_session",
        "features.multi_agent_v2.enabled",
        "features.multi_agent_v2.tool_namespace",
        "features.multi_agent_v2.max_concurrent_threads_per_session",
    )
    for dotted in dotted_keys:
        cleaned, n = re.subn(
            rf'^[ \t]*{re.escape(dotted)}\s*=\s*[^\r\n]*(?:\r?\n|$)',
            '', cleaned, flags=re.MULTILINE)
        if n:
            changed = True
    if changed:
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned, changed


def _get_section_bounds(content: str, section_name: str) -> tuple[int, int] | None:
    """Return the exact TOML section span, excluding the next section."""
    header = re.search(
        rf'^\[{re.escape(section_name)}\][ \t]*(?:\r?\n|$)',
        content,
        re.MULTILINE,
    )
    if not header:
        return None
    after = content[header.end():]
    next_section = re.search(r'^\[[^\r\n]+\][ \t]*(?:\r?\n|$)', after, re.MULTILINE)
    end = header.end() + (next_section.start() if next_section else len(after))
    return header.start(), end


def _ensure_section(content: str, section_name: str) -> tuple[str, bool]:
    """Ensure a TOML section exists before any implicit child table."""
    if _get_section_bounds(content, section_name) is not None:
        return content, False

    block = f"[{section_name}]\n"
    if "." in section_name:
        parent_name = section_name.rsplit(".", 1)[0]
        parent_bounds = _get_section_bounds(content, parent_name)
        if parent_bounds:
            insertion = parent_bounds[1]
            before = content[:insertion].rstrip("\n")
            after = content[insertion:].lstrip("\n")
            suffix = f"\n\n{after}" if after else "\n"
            return before + "\n\n" + block + suffix, True

    first_child = re.search(
        rf'^\[{re.escape(section_name)}\.[^\r\n]+\]', content, re.MULTILINE)
    first_section = re.search(r'^\[[^\r\n]+\]', content, re.MULTILINE)
    insertion = first_child or first_section
    if insertion:
        before = content[:insertion.start()].rstrip("\n")
        separator = "\n\n" if before else ""
        return before + separator + block + content[insertion.start():], True

    before = content.rstrip("\n")
    separator = "\n\n" if before else ""
    return before + separator + block, True


def _upsert_section_key(
    content: str, section_name: str, key: str, value: str,
) -> tuple[str, bool]:
    """Set one single-line key in an existing TOML section."""
    bounds = _get_section_bounds(content, section_name)
    if bounds is None:
        raise ValueError(f"目标 TOML section 不存在: [{section_name}]")

    section_start, section_end = bounds
    scope = content[section_start:section_end]
    key_match = re.search(
        rf'^[ \t]*{re.escape(key)}\s*=\s*[^\r\n]*(?:\r?\n|$)',
        scope,
        re.MULTILINE,
    )
    new_line = f"{key} = {value}\n"
    if key_match:
        old_line = key_match.group(0)
        if old_line == new_line:
            return content, False
        start = section_start + key_match.start()
        end = section_start + key_match.end()
        return content[:start] + new_line + content[end:], True

    header_end = content.find("\n", section_start, section_end)
    header_end = section_end if header_end < 0 else header_end + 1
    return content[:header_end] + new_line + content[header_end:], True


def _remove_section_keys(
    content: str, section_name: str, keys: tuple[str, ...],
) -> tuple[str, bool]:
    """Remove all managed key lines from one exact TOML section."""
    bounds = _get_section_bounds(content, section_name)
    if bounds is None:
        return content, False

    section_start, section_end = bounds
    scope = content[section_start:section_end]
    changed = False
    for key in keys:
        scope, count = re.subn(
            rf'^[ \t]*{re.escape(key)}\s*=\s*[^\r\n]*(?:\r?\n|$)',
            "",
            scope,
            flags=re.MULTILINE,
        )
        changed = changed or bool(count)
    return content[:section_start] + scope + content[section_end:], changed


def _ensure_feature_bool(content: str, key: str) -> tuple[str, bool]:
    """Ensure ``[features]`` section has ``{key} = true``. Returns (content, changed)."""
    content, section_added = _ensure_section(content, "features")
    content, key_changed = _upsert_section_key(content, "features", key, "true")
    return content, section_added or key_changed


def _remove_feature_key(content: str, key: str) -> tuple[str, bool]:
    """Remove a key from ``[features]`` section. Returns (content, changed)."""
    feat = re.search(r'^\[features\]', content, re.MULTILINE)
    if not feat:
        return content, False
    after = content[feat.end():]
    ns = re.search(r'^\[[\w]', after, re.MULTILINE)
    scope = after[:ns.start()] if ns else after
    m = re.search(rf'^{re.escape(key)}\s*=\s*\S+\s*\n?', scope, re.MULTILINE)
    if not m:
        return content, False
    abs_start = feat.end() + m.start()
    abs_end = feat.end() + m.end()
    content = content[:abs_start] + content[abs_end:]
    # Clean up empty [features] section
    feat2 = re.search(r'^\[features\]\s*\n', content, re.MULTILINE)
    if feat2:
        after2 = content[feat2.end():]
        ns2 = re.search(r'^\[[\w]', after2, re.MULTILINE)
        scope2 = after2[:ns2.start()] if ns2 else after2
        if not scope2.strip():
            end2 = feat2.end() + (ns2.start() if ns2 else len(after2))
            content = content[:feat2.start()] + content[end2:]
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content, True


def _configure_codex_csv_batch(dest_dir: Path) -> None:
    """Ensure the managed Codex multi-agent V2 and CSV settings are present."""
    config_path = dest_dir / "config.toml"
    content = ""
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")
    changed = False

    content, did_clean = _cleanup_codex_agents_dotted(content)
    changed = changed or did_clean

    content, section_added = _ensure_section(content, "agents")
    changed = changed or section_added
    content, old_agents_removed = _remove_section_keys(
        content,
        "agents",
        ("max_threads", "max_depth", "interrupt_message"),
    )
    changed = changed or old_agents_removed
    content, agents_limit_changed = _upsert_section_key(
        content,
        "agents",
        "max_concurrent_threads_per_session",
        "10",
    )
    changed = changed or agents_limit_changed

    content, fanout_added = _ensure_feature_bool(content, "enable_fanout")
    changed = changed or fanout_added

    content, v2_section_added = _ensure_section(content, "features.multi_agent_v2")
    changed = changed or v2_section_added
    content, old_v2_removed = _remove_section_keys(
        content,
        "features.multi_agent_v2",
        ("enabled", "tool_namespace", "max_concurrent_threads_per_session"),
    )
    changed = changed or old_v2_removed
    v2_values = (
        ("hide_spawn_agent_metadata", "true"),
        ("expose_spawn_agent_model_overrides", "false"),
        ("min_wait_timeout_ms", "50000"),
        ("default_wait_timeout_ms", "120000"),
        ("max_wait_timeout_ms", "240000"),
    )
    v2_changes = False
    for key, value in v2_values:
        content, key_changed = _upsert_section_key(
            content, "features.multi_agent_v2", key, value)
        v2_changes = v2_changes or key_changed
    changed = changed or v2_changes

    if changed:
        _validate_toml(content)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(content, encoding="utf-8")
        print(_msg(
            "  已配置多代理: [agents] 并发上限=10, [features.multi_agent_v2] 等待与派生策略已更新",
            "  Configured multi-agent: [agents] concurrency=10 and [features.multi_agent_v2] wait/spawn policy updated"))


# ---------------------------------------------------------------------------
# Codex developer_instructions — elevate HelloAGENTS routing to developer role
# ---------------------------------------------------------------------------

_CODEX_DEVELOPER_INSTRUCTIONS = """\
CRITICAL: As the main agent, strictly follow HelloAGENTS protocol — never skip \
routing, evaluation, or G3 format rules. Spawned sub-agents are exempt: execute \
assigned tasks directly, without routing, evaluation, scoring, or G3 format.

Sub-agent standing authorization: Installing/enabling HelloAGENTS and loading \
its AGENTS.md/G9/G10 workflow is the user's explicit standing request to use \
sub-agents whenever HelloAGENTS automatic orchestration conditions are met. If \
a sub-agent tool says spawning requires the user to explicitly ask for \
sub-agents, treat the active HelloAGENTS workflow trigger as satisfying that \
requirement. Do not ask the user to repeat "sub-agent" or "parallel agent" in \
the current message. On Codex, automatic orchestration also requires the \
efficiency/necessity gate in rules/subagent-codex.md: default to the main agent \
or parallel tools; spawn only when it clearly improves wall-clock/context \
efficiency or is necessary (complex multi-brainstormer, complex core/security \
review with ≥2 review units, or user-explicit parallel/sub-agent request). Do \
not spawn explorers merely because ≥2 semantic domains exist, and do not rescan \
with multi-explorer when the knowledge base or existing evidence already \
supports planning. Automatic orchestration starts only after candidate \
semantic filtering leaves enough launchable sub-agents for the Codex scene \
thresholds, the efficiency/necessity gate passes, and at least two actually \
start for ordinary batches. With fewer than the scene threshold, do not spawn; \
if only one starts, request handoff and converge it through the host-supported \
stop/reclaim mechanism. Without an explicit close API, verify a terminal/stopped \
state before taking over; otherwise block overlapping takeover and record the \
capability limitation. Tool or platform \
unavailability after the count gate passes is a recorded orchestration failure, \
not a candidate filter. Gate failure is normal non-trigger, not [降级执行]. \
Complex DESIGN brainstorming requires at least three actual brainstormer \
starts and three usable agent-authored proposals before comparison. An explicit \
manual single-role call is delegation, not automatic \
orchestration. Only skip spawning when the workflow/Codex gate trigger is not \
met, the user explicitly disables sub-agents, the platform/tool is unavailable \
after discovery, or a real spawn attempt fails. If the initial tool list does \
not show spawn_agent or spawn_agents_on_csv, search/discover sub-agent tools \
first and record the discovery result before downgrading.

Codex spawn compatibility: For named Codex agents, prefer \
spawn_agent(agent_type="...", prompt="...") with a self-contained context in \
the prompt. Do not combine agent_type with fork_context by default. If a \
fork_context argument/schema failure or agent_type+fork_context invalid \
combination occurs, it is not final failure evidence until the same agent_type \
has been retried with fork_context omitted and the required context embedded in \
the prompt. This avoids a first incompatible spawn attempt before retrying.

Codex reasoning effort policy: reasoning_effort is selected at invocation time \
and is independent of TASK_COMPLEXITY, spawn thresholds, concurrency, wait \
budgets, handoff, and EHRB. Canonical values are low, medium, high, xhigh, \
and max; normalize the user-facing alias "middle" to "medium" and never send \
"middle" to the tool. Use low for trivial tasks, medium for simple tasks, \
high for ordinary/default tasks, xhigh for complex tasks, and max only for \
exceptional complex tasks with at least two escalation signals including one \
architecture, boundary, or risk signal. Pass reasoning_effort only when the \
current spawn schema supports the requested value; otherwise omit it and record \
the fallback. For a value-specific argument error, retry once with the same \
agent_type and self-contained prompt but without reasoning_effort. CSV batches \
use one effort for homogeneous rows; group heterogeneous rows when the API \
does not support per-row effort. HelloAGENTS does not own a spawn_agent or CSV \
wrapper, so this is an invocation contract for the parent agent, not a host-level \
payload validator. When a fallback occurs, record requested/applied/fallback in \
tasks.md execution logs or the acceptance report; do not claim the host applied \
the requested value when the schema rejected or omitted it.

Complex coding checkpoint-batch policy: When TASK_COMPLEXITY=complex and tasks.md explicitly declares @execution_strategy: checkpoint-batch, select only DAG-ready tasks for the current batch. Use at most 3 tasks with no risk signal, at most 2 with context_near_limit or output_scope_large, and at most 1 with recoverable risks such as agent_wait_degraded or compaction_state_missing. package_incomplete blocks the batch before execution and cannot be bypassed with a single task. Implement and verify the current batch before unlocking downstream tasks, then update tasks.md and the optional .status.json.pipeline. Keep each batch response short: completed scope, verification result, blockers, and next batch only; never dump full files, diffs, or historical agent output. simple, moderate, and lightweight tasks keep their existing fast path.

If context was compressed during the session (previous messages were summarized, \
not at session start): Immediately read {KB_ROOT}/plan/*/tasks.md and the \
package .status.json (specifically the current status/pipeline summary) to restore \
workflow state (all G6-defined state variables: \
workflow variables, task complexity variables, knowledge base and package \
variables). Combine restored state with current user input to determine actual \
current state and correct next action, avoiding incorrect re-evaluation or stage \
confusion. Continue from interruption point if workflow should proceed (user \
input is task-related or continuation request), or enter routing if user \
requests new task.\
"""

def _developer_instructions_span(content: str) -> tuple[int, int] | None:
    """Locate a top-level TOML string assignment without interpreting it."""
    match = re.search(r'^developer_instructions\s*=\s*', content, re.MULTILINE)
    if not match:
        return None
    start = match.start()
    value_start = match.end()
    quote = content[value_start:value_start + 3]
    if quote in {'"""', "'''"}:
        closing = content.find(quote, value_start + 3)
        if closing < 0:
            return None
        return start, closing + 3
    if value_start >= len(content) or content[value_start] not in {'"', "'"}:
        return None
    delimiter = content[value_start]
    escaped = False
    for index in range(value_start + 1, len(content)):
        char = content[index]
        if delimiter == '"' and char == "\\" and not escaped:
            escaped = True
            continue
        if char == delimiter and not escaped:
            return start, index + 1
        if char in "\r\n" and not escaped:
            return None
        escaped = False
    return None


def _validate_toml(content: str) -> None:
    """Reject writes that would leave an invalid Codex TOML file."""
    if tomllib is not None:
        tomllib.loads(content)


def _configure_codex_developer_instructions(dest_dir: Path) -> bool:
    """Ensure config.toml has developer_instructions with HelloAGENTS protocol."""
    config_path = dest_dir / "config.toml"
    content = ""
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")

    toml_val = f'developer_instructions = """\n{_CODEX_DEVELOPER_INSTRUCTIONS}\n"""'

    # Check if existing developer_instructions is user-defined (not ours)
    span = _developer_instructions_span(content)
    if "developer_instructions" in content and span is None:
        raise ValueError("无法安全定位现有 developer_instructions")
    if span:
        existing = content[span[0]:span[1]]
        if "HelloAGENTS" not in existing:
            # User-defined content — backup before overwriting
            backup_path = config_path.parent / "developer_instructions.bak"
            if backup_path.exists() or backup_path.is_symlink():
                raise ValueError("developer_instructions 备份路径已存在")
            backup_path.write_text(existing, encoding="utf-8")
            print(_msg(
                f"  ⚠ 已备份现有 developer_instructions 到: {backup_path}",
                f"  ⚠ Backed up existing developer_instructions to: {backup_path}"))

    # Remove existing developer_instructions (ours or user's) and trailing blanks
    if span:
        end = span[1]
        while end < len(content) and content[end] in '\n\r':
            end += 1
        content = content[:span[0]] + content[end:]
        content = re.sub(r'\n{3,}', '\n\n', content)

    # Insert before notify (if exists) or before first section
    notify_match = re.search(r'^notify\s*=', content, re.MULTILINE)
    if notify_match:
        # Insert before notify
        content = content[:notify_match.start()] + toml_val + "\n\n" + content[notify_match.start():]
    else:
        # No notify, insert before first section
        first_section = re.search(r'^\[[\w]', content, re.MULTILINE)
        if first_section:
            content = content[:first_section.start()] + toml_val + "\n\n" + content[first_section.start():]
        else:
            # No sections, append at end
            content = content.rstrip() + "\n\n" + toml_val + "\n"

    _validate_toml(content)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    print(_msg("  已配置 developer_instructions（HelloAGENTS 完整恢复协议）",
               "  Configured developer_instructions (HelloAGENTS recovery protocol)"))
    return True


def _remove_codex_developer_instructions(dest_dir: Path) -> bool:
    """Remove managed instructions and restore a backed-up user value."""
    config_path = dest_dir / "config.toml"
    if not config_path.exists():
        return False
    content = config_path.read_text(encoding="utf-8")

    span = _developer_instructions_span(content)
    if not span or "HelloAGENTS" not in content[span[0]:span[1]]:
        return False

    # Remove the entire key-value pair and trailing blank lines
    end = span[1]
    while end < len(content) and content[end] in '\n\r':
        end += 1
    content = content[:span[0]] + content[end:]
    content = re.sub(r'\n{3,}', '\n\n', content)

    backup_path = dest_dir / "developer_instructions.bak"
    if backup_path.is_file() and not backup_path.is_symlink():
        backup = backup_path.read_text(encoding="utf-8").strip()
        backup_span = _developer_instructions_span(backup)
        if backup_span != (0, len(backup)):
            return False
        content = _insert_before_first_section(content, backup)

    _validate_toml(content)
    config_path.write_text(content, encoding="utf-8")
    if backup_path.is_file() and not backup_path.is_symlink():
        backup_path.unlink()
    return True


# ---------------------------------------------------------------------------
# Codex notify hook
# ---------------------------------------------------------------------------

def _resolve_codex_notify_argv(dest_dir: Path) -> list[str]:
    """Resolve notify command to argv tokens for Codex CLI.

    Codex CLI ``notify`` is an argv array — each element is a separate token,
    and Codex appends the JSON payload as the last argument.
    """
    scripts_dir = (dest_dir / PLUGIN_DIR_NAME / "scripts").as_posix()
    script_path = f"{scripts_dir}/{CODEX_NOTIFY_SCRIPT}"
    return [get_python_cmd(), script_path]


def _configure_codex_notify(dest_dir: Path) -> None:
    """Add HelloAGENTS notify hook to Codex CLI config.toml.

    This key is fully managed by HelloAGENTS — any existing content is
    overwritten on install/update. User-defined notify will be backed up.
    """
    config_path = dest_dir / "config.toml"
    content = ""
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")

    argv = _resolve_codex_notify_argv(dest_dir)
    # Format as TOML array: notify = ["python", "path/to/script.py"]
    toml_elements = ", ".join(f'"{token}"' for token in argv)
    notify_line = f'notify = [{toml_elements}]'

    # Check for existing notify (string or array format)
    m_str = re.search(r'^notify\s*=\s*"([^"]*)"', content, re.MULTILINE)
    m_arr = re.search(r'^notify\s*=\s*\[([^\]]*)\]', content, re.MULTILINE)

    existing = m_str or m_arr
    if existing:
        existing_val = existing.group(0)
        # Backup if user-defined (not HelloAGENTS)
        if "helloagents" not in existing_val.lower():
            backup_path = config_path.parent / "notify.bak"
            backup_path.write_text(existing_val, encoding="utf-8")
            print(_msg(f"  ⚠ 已备份现有 notify 到: {backup_path}",
                       f"  ⚠ Backed up existing notify to: {backup_path}"))

        # Remove existing notify (match trailing newline too)
        content = re.sub(r'^notify\s*=\s*(?:"[^"]*"|\[[^\]]*\])\s*\n?', '', content, count=1, flags=re.MULTILINE)

    # Add new notify
    content = _insert_before_first_section(content, notify_line)
    config_path.write_text(content, encoding="utf-8")
    print(_msg("  已配置 notify hook (config.toml)",
               "  Configured notify hook (config.toml)"))


def _remove_codex_notify(dest_dir: Path) -> bool:
    """Remove HelloAGENTS notify hook from config.toml. Returns True if removed."""
    config_path = dest_dir / "config.toml"
    if not config_path.exists():
        return False

    try:
        content = config_path.read_text(encoding="utf-8")
    except Exception as e:
        print(_msg(f"  ⚠ 无法读取 {config_path}: {e}",
                   f"  ⚠ Cannot read {config_path}: {e}"))
        return False

    # Try array format first, then old string format
    m_arr = re.search(r'^notify\s*=\s*\[([^\]]*)\]', content, re.MULTILINE)
    m_str = re.search(r'^notify\s*=\s*"([^"]*)"', content, re.MULTILINE)

    matched = None
    if m_arr and "helloagents" in m_arr.group(1):
        matched = r'^notify\s*=\s*\[[^\]]*\]\n?\n?'
    elif m_str and "helloagents" in m_str.group(1):
        matched = r'^notify\s*=\s*"[^"]*"\n?\n?'

    if not matched:
        return False

    content = re.sub(matched, '', content, count=1, flags=re.MULTILINE)
    try:
        config_path.write_text(content, encoding="utf-8")
    except PermissionError:
        print(_msg(f"  ⚠ 无法写入 {config_path}（文件被占用，请关闭 Codex CLI 后重试）",
                   f"  ⚠ Cannot write {config_path} (file locked, close Codex CLI and retry)"))
        return False
    print(_msg("  已移除 notify hook (config.toml)",
               "  Removed notify hook (config.toml)"))
    return True


# ---------------------------------------------------------------------------
# Codex TUI notification method (suppress BEL bell)
# ---------------------------------------------------------------------------

def _configure_codex_tui_notification(dest_dir: Path) -> None:
    """Set tui.notification_method = "osc9" to suppress BEL bell."""
    config_path = dest_dir / "config.toml"
    content = ""
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")

    # Check for existing notification_method (dotted or in [tui] section)
    dotted_match = re.search(r'tui\.notification_method\s*=\s*"([^"]*)"', content)

    tui_section_match = re.search(r'^\[tui\]', content, re.MULTILINE)
    section_match = None
    if tui_section_match:
        after = content[tui_section_match.end():]
        next_sec = re.search(r'^\[[\w]', after, re.MULTILINE)
        scope = after[:next_sec.start()] if next_sec else after
        section_match = re.search(r'^notification_method\s*=\s*"([^"]*)"', scope, re.MULTILINE)

    existing = dotted_match or section_match
    if existing:
        existing_val = existing.group(1)
        # Backup if user-defined (not "osc9")
        if existing_val != "osc9":
            backup_path = config_path.parent / "tui_notification.bak"
            backup_path.write_text(f'notification_method = "{existing_val}"', encoding="utf-8")
            print(_msg(f"  ⚠ 已备份现有 tui.notification_method 到: {backup_path}",
                       f"  ⚠ Backed up existing tui.notification_method to: {backup_path}"))

        # Remove existing — section form first to avoid stale positions
        # (removing dotted form first would shift content, invalidating
        # tui_section_match/section_match positions captured above)
        if section_match and tui_section_match:
            start = tui_section_match.end() + section_match.start()
            end = start + len(section_match.group(0))
            content = content[:start] + content[end:]
            content = re.sub(r'\n{3,}', '\n\n', content)
        if dotted_match:
            content = re.sub(r'tui\.notification_method\s*=\s*"[^"]*"\s*\n?', '', content)

    # Add new value in [tui] section
    tui_match = re.search(r'^\[tui\]', content, re.MULTILINE)
    if tui_match:
        content = (content[:tui_match.end()]
                   + '\nnotification_method = "osc9"'
                   + content[tui_match.end():])
    else:
        section = '[tui]\nnotification_method = "osc9"\n'
        first_sec = re.search(r'^\[[\w]', content, re.MULTILINE)
        if first_sec:
            content = content[:first_sec.start()] + section + "\n" + content[first_sec.start():]
        else:
            content = content.rstrip() + "\n\n" + section

    config_path.write_text(content, encoding="utf-8")
    print(_msg("  已配置 tui.notification_method = osc9（抑制 BEL 铃声）",
               "  Configured tui.notification_method = osc9 (suppress BEL bell)"))


def _remove_codex_tui_notification(dest_dir: Path) -> bool:
    """Remove tui.notification_method from config.toml if "osc9". Returns True if removed."""
    config_path = dest_dir / "config.toml"
    if not config_path.exists():
        return False

    content = config_path.read_text(encoding="utf-8")

    # Only remove if it's our "osc9" value
    m = re.search(r'^notification_method\s*=\s*"osc9"\s*\n?', content, re.MULTILINE)
    if not m:
        # Also check dotted form
        m = re.search(r'^tui\.notification_method\s*=\s*"osc9"\s*\n?', content, re.MULTILINE)
    if not m:
        return False

    content = content[:m.start()] + content[m.end():]

    # Clean up empty [tui] section if nothing left in it
    tui_match = re.search(r'^\[tui\]\s*\n', content, re.MULTILINE)
    if tui_match:
        after = content[tui_match.end():]
        next_sec = re.search(r'^\[[\w]', after, re.MULTILINE)
        scope = after[:next_sec.start()] if next_sec else after
        if not scope.strip():
            # Section is empty — remove it
            end = tui_match.end() + (next_sec.start() if next_sec else len(after))
            content = content[:tui_match.start()] + content[end:]

    content = re.sub(r'\n{3,}', '\n\n', content)
    config_path.write_text(content, encoding="utf-8")
    print(_msg("  已移除 tui.notification_method (config.toml)",
               "  Removed tui.notification_method (config.toml)"))
    return True

