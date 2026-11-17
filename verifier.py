# Copyright 2026 Kaleb Coleman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Pre-done check that deliverable paths from the instruction exist and open.

The check is generic. It does not look at task ids, grader files, or the
harness's own artifacts. It only reads paths the instruction itself names,
then stats those paths inside the task container. It never writes a file and
never raises: a failed check is a note on the final message, and `done` still
goes out.
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Any

# Leave the deadline alone when less than this remains. The model turn has
# already been stopped; this only skips the file probe.
MIN_SECONDS = 20
MAX_PATHS = 12
MAX_MEMBERS_SHOWN = 12
# Skip a full CRC walk on archives larger than this. Listing members is enough.
MAX_ZIP_TEST_BYTES = 20_000_000

_EXTS = (
    "zip|docx|xlsx|xlsm|xls|pdf|ifc|dxf|dwg|csv|md|json|py|txt|pptx"
)
_FILE = rf"[\w.+-]+\.(?:{_EXTS})"
_ABS = re.compile(rf"(?<![\w./])(/(?:[\w.+-]+/)*{_FILE})\b")
_REL_OUT = re.compile(rf"(?<![\w./])((?:[\w.+-]+/)*output/{_FILE})\b")
_VERBS = re.compile(
    r"\b(?:creat\w*|writ\w*|sav\w*|deliver\w*|plac\w*|put|submit\w*|nam\w*)\b",
    re.IGNORECASE,
)
_TICK = re.compile(r"`([^`\n]+)`")
_SAFE = re.compile(r"^/[\w.+@/=-]+$")

# Runs in the task container. Paths are embedded as Python literals by the
# harness before this source is base64-encoded, so the shell never sees them.
_PROBE = r"""
import json, os, zipfile
PATHS = __PATHS__
out = []
for path in PATHS:
    rec = {"path": path}
    try:
        if not os.path.lexists(path):
            rec["status"] = "missing"
            out.append(rec)
            continue
        if os.path.islink(path):
            rec["status"] = "symlink"
            out.append(rec)
            continue
        if not os.path.isfile(path):
            rec["status"] = "not_a_file"
            out.append(rec)
            continue
        size = os.path.getsize(path)
        rec["size"] = size
        if size <= 0:
            rec["status"] = "empty"
            out.append(rec)
            continue
        ext = path.rsplit(".", 1)[-1].lower()
        problems = []
        if ext in {"zip", "docx", "xlsx", "xlsm", "pptx"}:
            if not zipfile.is_zipfile(path):
                problems.append("not a zip archive")
            else:
                with zipfile.ZipFile(path) as zf:
                    names = zf.namelist()
                    bases = []
                    for name in names:
                        base = name.rstrip("/").rsplit("/", 1)[-1]
                        if base and base not in bases:
                            bases.append(base)
                    rec["member_count"] = len(names)
                    rec["members"] = bases[:__MAX_MEMBERS__]
                    if ext != "zip" and "[Content_Types].xml" not in names:
                        problems.append("missing [Content_Types].xml")
                    if size <= __MAX_ZIP_TEST__ :
                        bad = zf.testzip()
                        if bad:
                            problems.append("corrupt member " + bad)
                    else:
                        rec["note"] = "archive larger than the integrity walk"
        elif ext == "pdf":
            with open(path, "rb") as fh:
                if not fh.read(8).startswith(b"%PDF"):
                    problems.append("missing %PDF header")
        elif ext == "ifc":
            with open(path, "rb") as fh:
                if b"ISO-10303-21" not in fh.read(4096):
                    problems.append("missing ISO-10303-21 header")
        elif ext == "py":
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                compile(fh.read(), path, "exec")
        rec["status"] = "invalid" if problems else "ok"
        if problems:
            rec["problems"] = problems
    except Exception as exc:  # noqa: BLE001 - one bad path must not abort the rest
        rec["status"] = "invalid"
        rec["problems"] = [type(exc).__name__ + ": " + str(exc)]
    out.append(rec)
print("VERIFY_JSON:" + json.dumps(out))
"""


def extract_deliverable_paths(instruction: str, workdir: str) -> list[str]:
  """Returns file paths the instruction tells the agent to produce.

  Absolute paths are kept when they sit in an ``output`` or ``submission``
  directory, or when a write/save/create verb names them. A backticked file
  name with no directory is joined to ``workdir`` only in that same verb
  context. ``output/<file>`` is always joined to ``workdir``.

  Args:
    instruction: Task instruction text.
    workdir: Task working directory from the protocol message.

  Returns:
    Up to ``MAX_PATHS`` absolute paths, in order of first mention.
  """
  text = instruction or ""
  root = workdir if workdir.startswith("/") else "/"
  found: list[str] = []

  def add(path: str) -> None:
    parts = path.split("/")
    # Drop traversal. `.` is a legal character inside a file name, so this
    # checks whole segments rather than the character.
    if any(part in ("", ".", "..") for part in parts[1:]):
      return
    norm = os.path.normpath(path)
    if norm != path or not _SAFE.fullmatch(norm):
      return
    if norm not in found:
      found.append(norm)

  for match in _ABS.finditer(text):
    path = match.group(1)
    prefix = text[max(0, match.start() - 120) : match.start()]
    if "/output/" in path or "/submission/" in path or _VERBS.search(prefix):
      add(path)
  for match in _REL_OUT.finditer(text):
    add(os.path.join(root, match.group(1)))
  for match in _TICK.finditer(text):
    name = match.group(1).strip()
    if "/" in name or not re.fullmatch(_FILE, name):
      continue
    prefix = text[max(0, match.start() - 80) : match.start()]
    if _VERBS.search(prefix):
      add(os.path.join(root, name))
    if len(found) >= MAX_PATHS:
      break
  return found[:MAX_PATHS]


def probe_command(paths: list[str]) -> str:
  """Returns a ``bash -c`` command that probes ``paths`` and prints JSON.

  Args:
    paths: Absolute file paths to stat inside the task container.

  Returns:
    A shell command that runs only the Python standard library.
  """
  source = (
      _PROBE.replace("__PATHS__", repr(list(paths)))
      .replace("__MAX_MEMBERS__", str(MAX_MEMBERS_SHOWN))
      .replace("__MAX_ZIP_TEST__", str(MAX_ZIP_TEST_BYTES))
  )
  encoded = base64.b64encode(source.encode()).decode("ascii")
  return (
      "python3 -c \"import base64; exec(base64.b64decode('" + encoded + "'))\""
  )


def parse_probe_output(output: str) -> list[dict[str, Any]] | None:
  """Parses the probe's ``VERIFY_JSON:`` line.

  Args:
    output: Combined stdout and stderr from the probe command.

  Returns:
    A list of per-path records, or ``None`` when the marker is absent.
  """
  for line in reversed((output or "").splitlines()):
    if line.startswith("VERIFY_JSON:"):
      try:
        data = json.loads(line[len("VERIFY_JSON:") :])
      except ValueError:
        return None
      if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
  return None


def render(records: list[dict[str, Any]]) -> str:
  """Formats probe records as a short appendix for ``done.final_message``.

  Args:
    records: Records returned by the in-container probe.

  Returns:
    A multi-line note. Empty when there is nothing to say.
  """
  if not records:
    return ""
  lines = ["Deliverable check (task container, before done):"]
  for rec in records:
    path = str(rec.get("path") or "?")
    status = str(rec.get("status") or "unknown")
    size = rec.get("size")
    detail = status
    if isinstance(size, int):
      detail += f", {size} bytes"
    if status == "ok" and rec.get("member_count") is not None:
      shown = rec.get("members") or []
      names = ", ".join(str(name) for name in shown)
      extra = ""
      count = rec.get("member_count")
      if isinstance(count, int) and len(shown) < count:
        extra = f", {count} entries"
      detail += f", archive [{names}]{extra}"
    problems = rec.get("problems") or []
    if problems:
      detail += "; " + "; ".join(str(item) for item in problems)
    if rec.get("note"):
      detail += f"; {rec['note']}"
    lines.append(f"- {path}: {detail}")
  lines.append(
      "This check confirms that named deliverable paths exist and open."
      " It does not score engineering constraints."
  )
  return "\n".join(lines)


async def safe_check(session: Any) -> str:
  """Probes deliverable paths and returns a note. Never raises.

  Args:
    session: Task session with ``instruction``, ``workdir``, ``time_left``,
      ``exec``, and ``log``.

  Returns:
    A note to append to the final message, or ``""`` when there is nothing
    to add (no paths named, no time left, or the probe itself failed).
  """
  try:
    left = session.time_left()
    if left is not None and left < MIN_SECONDS:
      await _log(session, f"verifier: skipped, {left:.0f}s left")
      return ""
    paths = extract_deliverable_paths(
        getattr(session, "instruction", "") or "",
        getattr(session, "workdir", "") or "/",
    )
    if not paths:
      await _log(session, "verifier: no deliverable path named in the instruction")
      return ""
    await _log(session, "verifier: checking " + ", ".join(paths))
    result = await session.exec(probe_command(paths), timeout_sec=60)
    if result.get("timed_out"):
      await _log(session, "verifier: probe timed out")
      return ""
    records = parse_probe_output(result.get("output") or "")
    if records is None:
      tail = (result.get("output") or "")[-400:]
      await _log(
          session,
          f"verifier: probe exit {result.get('exit_code')}: {tail}",
      )
      return ""
    note = render(records)
    if note:
      await _log(session, note[:2000])
    return note
  except Exception as exc:  # noqa: BLE001 - the check must not block done
    await _log(session, f"verifier: skipped ({type(exc).__name__}: {exc})")
    return ""


async def _log(session: Any, text: str) -> None:
  log = getattr(session, "log", None)
  if log is None:
    return
  try:
    await log(text[:2000])
  except Exception:  # noqa: BLE001 - logging is best-effort
    return
