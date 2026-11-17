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

"""Local checks for the pre-done deliverable probe. No model calls."""

from __future__ import annotations

import asyncio
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import verifier  # noqa: E402

SMOKE = (
    "Create a file named `hello.txt` in the current working directory (`/app`)"
    " whose entire content is the single line:\n\nHELLO\n\nDo not create any"
    " other files. When the file exists, reply with the word done and stop."
)


class ExtractTests(unittest.TestCase):

  def test_smoke_names_hello_under_workdir(self):
    paths = verifier.extract_deliverable_paths(SMOKE, "/app")
    self.assertEqual(paths, ["/app/hello.txt"])

  def test_output_zip_and_ignores_reference_pdf(self):
    instruction = textwrap.dedent(
        """
        You are working in `/filesystem/example_blind`.
        See `/usr/share/doc/example.pdf` and read `notes.md` first.
        Write the final deliverable to
        `/filesystem/example_blind/output/submission.zip`.
        Also refresh output/design_basis.md as you go.
        """
    )
    paths = verifier.extract_deliverable_paths(instruction, "/filesystem/example_blind")
    self.assertEqual(
        paths,
        [
            "/filesystem/example_blind/output/submission.zip",
            "/filesystem/example_blind/output/design_basis.md",
        ],
    )

  def test_save_verb_keeps_absolute_memo(self):
    instruction = "Save the memo to `/filesystem/ALN-108_Response.docx`."
    paths = verifier.extract_deliverable_paths(instruction, "/app")
    self.assertEqual(paths, ["/filesystem/ALN-108_Response.docx"])

  def test_rejects_parent_segments(self):
    instruction = "Write the file to `/app/output/../../etc/passwd.txt`."
    # The regex does not treat `..` as a path segment, so nothing is extracted.
    self.assertEqual(verifier.extract_deliverable_paths(instruction, "/app"), [])


class ProbeTests(unittest.TestCase):

  def test_probe_classifies_files(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = pathlib.Path(tmp)
      good = root / "hello.txt"
      good.write_text("HELLO\n", encoding="utf-8")
      empty = root / "empty.csv"
      empty.write_text("", encoding="utf-8")
      link = root / "link.txt"
      link.symlink_to(good)
      script = root / "solution.py"
      script.write_text("def build():\n  return 1\n", encoding="utf-8")
      broken = root / "broken.py"
      broken.write_text("def build(:\n", encoding="utf-8")
      ifc = root / "model.ifc"
      ifc.write_text("ISO-10303-21;\nENDSEC;\n", encoding="utf-8")
      archive = root / "submission.zip"
      with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("deck_design.xlsx", b"pk")
        zf.writestr("design_basis.md", b"# basis\n")
      missing = root / "missing.docx"
      paths = [
          str(good),
          str(empty),
          str(link),
          str(script),
          str(broken),
          str(ifc),
          str(archive),
          str(missing),
          str(root),  # a directory
      ]
      proc = subprocess.run(
          ["bash", "-c", verifier.probe_command(paths)],
          check=False,
          capture_output=True,
          text=True,
      )
      self.assertEqual(proc.returncode, 0, proc.stderr)
      records = verifier.parse_probe_output(proc.stdout)
      self.assertIsNotNone(records)
      by_path = {rec["path"]: rec for rec in records}
      self.assertEqual(by_path[str(good)]["status"], "ok")
      self.assertEqual(by_path[str(empty)]["status"], "empty")
      self.assertEqual(by_path[str(link)]["status"], "symlink")
      self.assertEqual(by_path[str(script)]["status"], "ok")
      self.assertEqual(by_path[str(broken)]["status"], "invalid")
      self.assertEqual(by_path[str(ifc)]["status"], "ok")
      self.assertEqual(by_path[str(archive)]["status"], "ok")
      self.assertEqual(by_path[str(archive)]["member_count"], 2)
      self.assertEqual(by_path[str(missing)]["status"], "missing")
      self.assertEqual(by_path[str(root)]["status"], "not_a_file")
      note = verifier.render(records)
      self.assertIn(str(archive), note)
      self.assertIn("deck_design.xlsx", note)
      self.assertIn("does not score engineering constraints", note)


class SessionTests(unittest.TestCase):

  def test_safe_check_appends_note_and_swallows_exec_errors(self):

    class Boom:
      instruction = "Write `/app/output/submission.zip`."
      workdir = "/app"

      def time_left(self):
        return 100

      async def log(self, text):
        del text

      async def exec(self, command, timeout_sec=60):
        del command, timeout_sec
        raise RuntimeError("container went away")

    note = asyncio.run(verifier.safe_check(Boom()))
    self.assertEqual(note, "")

  def test_safe_check_skips_when_time_is_short(self):

    class Late:
      instruction = SMOKE
      workdir = "/app"
      logs: list[str]

      def __init__(self):
        self.logs = []

      def time_left(self):
        return 5

      async def log(self, text):
        self.logs.append(text)

      async def exec(self, command, timeout_sec=60):
        del command, timeout_sec
        raise AssertionError("probe must not run this close to the deadline")

    session = Late()
    note = asyncio.run(verifier.safe_check(session))
    self.assertEqual(note, "")
    self.assertTrue(any("skipped" in line for line in session.logs))

  def test_safe_check_against_a_local_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = pathlib.Path(tmp) / "hello.txt"
      path.write_text("HELLO\n", encoding="utf-8")

      class Local:
        workdir = tmp
        instruction = f"Create a file named `hello.txt` in `{tmp}`."
        logs: list[str]

        def __init__(self):
          self.logs = []

        def time_left(self):
          return None

        async def log(self, text):
          self.logs.append(text)

        async def exec(self, command, timeout_sec=60):
          proc = subprocess.run(
              ["bash", "-c", command],
              check=False,
              capture_output=True,
              text=True,
              timeout=timeout_sec,
          )
          return {
              "exit_code": proc.returncode,
              "output": proc.stdout + proc.stderr,
              "timed_out": False,
          }

      # The verb rule joins the backticked name to workdir.
      session = Local()
      note = asyncio.run(verifier.safe_check(session))
      self.assertIn(str(path), note)
      self.assertIn("ok", note)
      self.assertTrue(session.logs)


if __name__ == "__main__":
  unittest.main()
