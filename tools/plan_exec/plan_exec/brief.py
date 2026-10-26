"""Extract one task from a plan file as a brief.

Two plan shapes are supported:
- Section headings: ``### Task 2: Title`` with a body to the next
  heading of the same or a shallower level.
- OpenSpec checkbox tasks: ``- [ ] 2.3 Title`` with indented body
  lines. The body runs to the next checkbox at the same indent, the
  next heading, or a dedented non-blank line; blank lines stay.

Fenced blocks (``` or ~~~) hide their content from the stop rules, so a
fenced ``# comment`` or a literal ``- [ ]`` line inside a body never
ends it.
"""
import re
from pathlib import Path

_SECTION_RE = re.compile(r"^(#{1,6})\s+Task\s+(\d+)\s*[:.\-]?\s*(.*)$")
_CHECKBOX_RE = re.compile(r"^(\s*)-\s\[\s\]\s+(\d+(?:\.\d+)*)\s+(.*)$")


class TaskNotFound(Exception):
    """The requested task id does not exist in the plan."""


def _parts(task_id):
    return [int(part) for part in str(task_id).split(".")]


def _task_key(task_id):
    """Normalize a task id: '02.03' and '2.3' are the same task."""
    try:
        return ".".join(str(part) for part in _parts(task_id))
    except ValueError as exc:
        raise TaskNotFound(f"non-numeric task id: {task_id!r}") from exc


def _pop_trailing_blanks(body):
    while body and not body[-1].strip():
        body.pop()
    return body


def _in_fence(line, fence):
    """Toggle the fenced-block state on a ``` or ~~~ marker line."""
    if line.strip().startswith(("```", "~~~")):
        return not fence
    return fence


def _section_body(lines, index, level):
    """Collect a section task body: to the next heading of the same or
    a shallower level, or end of file. Fenced content and its markers
    never end it. Trailing blank lines go."""
    body = []
    fence = False
    for line in lines[index + 1:]:
        will_fence = _in_fence(line, fence)
        heading = re.match(r"^(#{1,6})\s", line)
        if heading and len(heading.group(1)) <= level and not fence:
            break
        body.append(line)
        fence = will_fence
    return _pop_trailing_blanks(body)


def _checkbox_body(lines, index, indent):
    """Collect a checkbox task body: blank or deeper-indented lines,
    until a dedented non-blank line (a column-0 heading included) or the
    next checkbox at the same or shallower indent. Fenced content and
    its markers never end it."""
    body = []
    fence = False
    for line in lines[index + 1:]:
        will_fence = _in_fence(line, fence)
        inside = fence or will_fence
        stripped = line.strip()
        if not stripped:
            body.append(line)
            fence = will_fence
            continue
        checkbox = _CHECKBOX_RE.match(line)
        if checkbox and len(checkbox.group(1)) <= indent and not inside:
            break
        if not line.startswith(" ") and not inside:
            break
        body.append(line)
        fence = will_fence
    return _pop_trailing_blanks(body)


def find_task(text, task_id):
    """Return the lines of one task, or raise TaskNotFound."""
    key = _task_key(task_id)
    lines = text.splitlines()
    for index, line in enumerate(lines):
        section = _SECTION_RE.match(line)
        if section and str(int(section.group(2))) == key:
            return [line] + _section_body(lines, index, len(section.group(1)))
        checkbox = _CHECKBOX_RE.match(line)
        if checkbox and _task_key(checkbox.group(2)) == key:
            return [line] + _checkbox_body(lines, index, len(checkbox.group(1)))
    raise TaskNotFound(f"no task {key!r} in plan")


def write_brief(plan_path, task_id, out_dir):
    """Extract one task to <out_dir>/task-<id>-brief.md and return the path."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TaskNotFound(f"cannot read plan {plan_path}: {exc}") from exc
    body = "\n".join(find_task(text, task_id)) + "\n"
    target = Path(out_dir) / f"task-{_task_key(task_id)}-brief.md"
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    except OSError as exc:
        raise TaskNotFound(f"cannot write brief {target}: {exc}") from exc
    return target
