# Plan: raise the Pi + Opus 5.5 dev score

This is the plan for Kaleb's fork of the Pi on Claude Opus 5.5 starter
(`google-cloud/claude-opus-5-5`, entry name `my-harness`). It is based on the
published `artifacts/manifest.json` (created 2026-10-20, run ids `b96-r1` and
`run3b`) and on each task's `trajectory.json` and `final_message.md`. Grading
type and deliverable paths are the public labels in the competition kit's
`eval/dev_set.yaml`. This plan does not read graders, and the harness must not
either.

The published mean is **0.491** (29 tasks, sum of rewards / 29). Constraint
tasks use `s = 0.4 p + 0.6 G O'`. Any failed hard check sets `G = 0` and caps
that item at `0.4`. Rubric tasks are scored by an LLM judge that also reads
`done.final_message` when `final_message: true`.

Do not submit this commit as a scored entry. `artifacts/` is still the
starter's run. After `harness.py` changes, `python -m kit artifacts` warns
that the harness changed, and it also warns that the manifest was made with
another dev-set revision. Regenerate `artifacts/` with `eval/run.py` and
commit harness and artifacts together. Do not edit `artifacts/` by hand.

## Scores

| Reward | Grading | Files | Task | What the artifacts show |
|---:|---|---:|---|---|
| 0.000 | checks | 1 | data-hall-mep-routing | `solution.py` only. Agent reports a self-checked IFC, but guessed element classes, property sets, facing, joint clashes, and entry tolerance. Reward is 0, not a 0.4 cap, so the re-run model earned no partial credit. |
| 0.000 | checks | 1 | data-hall-mep-routing-offset | Same pattern. All three services were forced underfloor; entry points were offset to keep separation. |
| 0.000 | checks-judge | 0 | foundation-strategy | No `submission.zip`. 73 steps, last event is an in-progress `bash` edit of `opt.py`. Final message is the literal `[tool call]`. The grader does not read `final_message`, so an empty deliverable path is 0. `kit artifacts` marks this task empty. |
| 0.000 | rubric | 0 | solar-witness-test-package | 22 steps. Wiki.js returned "not authorized"; OpenProject returned unauthenticated. Final message is "Now the case tracking in OpenProject. Let me check API access." No package was written. The judge reads that message. |
| 0.208 | rubric | 1 | solar-supplemental-review | Memo exists, but the agent says the export folder was not writable and the file landed at the working-directory root. Queue record and application number were missing; signature lines were left blank. |
| 0.231 | rubric | 3 | pre-application-capacity-response | Letter was written, but the agent refused the 3.0 MW figure and answered 0.8 MW. The judge reads the memo and the summary. |
| 0.286 | checks | 1 | roof-deck-design | Zip written. Score sits under the 0.4 hard-gate cap. The writeup flags cell-boundary convention, chord vs edge-angle force, and how diaphragm deflection is measured. |
| 0.302 | checks-judge | 1 | eor-review-corrections | Zip written, under the cap. The writeup flags void vs valid comments, missing revision marks, whether the start day counts, and `NOT_APPLICABLE` vs `NON_CONCUR`. |
| 0.316 | checks | 1 | wind-diaphragm-shear | Zip written, under the cap. Uncertain readings: which reaction the table reports, quarter-point station side, torsion sign. |
| 0.316 | checks | 1 | seismic-diaphragm-shear | Zip written, under the cap. Uncertain readings: torsion factor on the east wall, which drag struts count, 1.4 anchorage factor. |
| 0.349 | checks | 1 | division-26-specifications | Zip written, under the cap. Spec text was tailored from UFGS; a hard miss in the workbook or a required section would zero `G`. |
| 0.353 | checks | 1 | mv-conveyance-study | Zip written, under the cap. The writeup flags the 160 A conduit limit and whether SS-1 counts as a unit substation for the 200 ft rule. |
| 0.383 | checks | 1 | data-hall-device-takeoff | Zip written, just under the cap. Assembly composition (GFCI, plaster rings, duct detectors) is the likely hard miss. |
| 0.461 | checks | 1 | cooling-water-flush-plan | Zip written and above 0.4, so the hard gate likely passed and the objective is only partly optimized. |
| 0.516 | rubric | 3 | shoring-design-verification | Memo package present. Remaining loss is judgment, not a missing file. |
| 0.532 | rubric | 2 | footing-settlement-verification | Memo present. |
| 0.537 | rubric | 1 | les-mesh-resolution | Note present. |
| 0.543 | rubric | 1 | engineers-estimate-check | Memo present. |
| 0.622 | rubric | 1 | emergency-spillway-check | Memo present. |
| 0.636 | rubric | 2 | fire-solve-convergence | Memo plus the runtime email. |
| 0.676 | rubric | 3 | fill-compaction-acceptance | Memo plus the workbook. |
| 0.692 | checks | 1 | heat-rejection-life-cycle-cost | Above the cap: hard checks likely passed; cost objective still short of the bound. |
| 0.806 | checks | 1 | frame-extension-method | Strong checks score. |
| 0.808 | rubric | 1 | fire-test-validation-memo | Strong rubric score. |
| 0.857 | rubric | 1 | landscape-sheet-revision | Strong rubric score. |
| 0.907 | checks-judge | 1 | lv-cable-sizing | Near the top of the checks-judge group. |
| 0.909 | rubric | 3 | permission-to-operate-memo | Strong rubric score. |
| 1.000 | rubric | 3 | backfeed-energization-reply | Full score. |
| 1.000 | checks | 1 | data-center-site-model | Full score on an IFC deliverable. Useful contrast with the two MEP tasks, which also build IFC but ship a generator script and scored 0. |

Group means on this run: checks 0.414 (12 tasks), checks-judge 0.403 (3), rubric 0.577 (14).

There is no per-constraint grader log in `artifacts/`. Scores at or under 0.4 on `checks` tasks are consistent with `G = 0`, not proof of which clause failed. The "what the artifacts show" column is the agent's own final message plus whether the graded path was exported.

## Where the points are

Four failure shapes, none of which should be patched by task id:

1. **Nothing at the graded path when the clock stops.** `foundation-strategy` was still editing a solver. `solar-witness-test-package` stopped while hunting an API login. A checks grader that does not read `final_message` scores a missing file as 0.
2. **A file is present and every hard check fails.** Both MEP tasks. The agent guessed the IFC contract (classes, property sets, facing, whether same-service joints clash, how tight "reaches the entry" is). `data-center-site-model` shows the same family of task can score 1.0 when the file matches the contract and the example in the task tree.
3. **One hard miss caps a finished zip at 0.4.** Roof deck, both diaphragm tasks, Division 26, the conveyance study, the device takeoff, and the EOR review all landed between 0.28 and 0.38. The writeups already name the rule reading they were unsure about. A second pass that re-derives those limits from the task files, and revises the zip when a reading fails, is worth more than a new optimizer.
4. **Rubric tasks with a weak or off-path memo.** Solar supplemental and the pre-application reply scored about 0.2 with files present. The judge reads the memo and the final summary. A summary that states the decision, the controlling numbers, the assumptions, and the exact paths is part of the score on every `final_message: true` task.

## Priority

### 1. Pre-`done` verifier (started in this commit)

Shipped now, on purpose small:

- `verifier.py` reads the instruction, not a task list. It keeps paths under `output/` or `submission/`, paths named by a write/save/create verb, and backticked file names in that same verb context (the smoke task's `hello.txt`).
- After Pi returns, and only if at least 20 seconds remain, one `exec` in the task container stats those paths. It rejects symlinks (graders ignore them), empty files, a missing zip or Office package header, a missing `ISO-10303-21` header, and a `.py` file that does not compile. Zip members are listed, not guessed.
- The note is appended to `final_message` and logged. The probe never writes a file and never raises, so `done` still goes out. `STOP_BEFORE_SEC` is 180 so the probe has time after Pi is stopped. On a short task, `taskbridge.time_share` shrinks that reserve to a quarter of the time left.
- The system note tells Pi to write the real deliverable early, to look for credentials before treating 401/403 as fatal, and to end with a summary a judge can grade alone.

Not shipped, and the next code change:

- If the probe reports `missing`, `empty`, `symlink`, or `invalid` and more than about three minutes remain, start **one** repair turn. Feed Pi the original instruction plus the probe note. Do not clear the files it already wrote. This is the same shape as the kit's `sample_submissions/plan-verify` worker/verifier loop, kept on Pi so MCP still works. `plan-verify` itself does not call task MCP servers.
- Reserve the last 10–15% of `agent_timeout_sec` for that repair, not only the 180 second file probe. Skip the repair when the reserve would be under two minutes, and send `done` with the files already on disk.
- For a `.py` deliverable, the repair turn may run the script once, writing to a path the instruction names or to a temp file the instruction's own CLI accepts. Then re-probe. Do not run it twice if the first run is slow. Do not import a grader.

The file probe does not know hard engineering constraints. Those have to be re-derived from the drawings, the spec, and any example file in the task tree. Teach that as a checklist the model writes for itself (`limit`, `where it is stated`, `how to measure`, `pass/fail`), then executes. Branch on the checklist, never on a task id or on a path that appears only in `dev_set.yaml`.

### 2. Reliability

- Keep the "write the graded path before the next experiment" rule. `foundation-strategy` is the example: a better footing solver with no zip scores 0.
- On cancel, `taskbridge` already sends `done` with the last summary. Keep that. Do not `sys.exit` out of `solve` after the model has spoken; a harness that errors before any model output is retried, and one that errors after output can still lose the summary if `final_message` is empty.
- Pi is already configured for six retries and a 60 second cap on retry delay. Leave 400s unretriable. Do not add web search or any host other than the model endpoint.
- Inject remaining time into the repair turn ("you have N minutes, write the files now"). The single long Pi session cannot see the clock unless the prompt says so up front.
- Smoke must stay green: the probe only reads, and the smoke grader checks `/app/hello.txt` contents plus a completed `done`, not the exact final text.

### 3. Libraries in the task container

`install` runs in the build container. Only `/opt/harness` is kept. The task container is a different machine with no network, and it cannot import `/opt/harness/venv`. Installing `ezdxf` or `ifcopenshell` into the serve venv does not make `python3` inside `exec` see them. The MEP trajectories already imported `ifcopenshell` successfully inside the task, so that image has it; other tasks may not.

When a task needs a library:

1. `python3 -c "import <name>"` in the task container.
2. If it imports, use it. Do not copy a second copy.
3. If it does not, copy a wheel that `install` downloaded under `/opt/harness` and `pip install --no-index` it, or unzip a pure-Python package and put it on `sys.path` from the script under test. `write_file` is capped at 10 MB per call; larger wheels go up with `append: true`. Prefer wheels that are pure Python (`openpyxl`, `ezdxf`) over a native `ifcopenshell` build unless step 1 failed.
4. Pin whatever `install` downloads. Do not leave versions floating. Record the pin in `requirements.txt` only when the serve container itself imports it, or in a separate `task-wheels.txt` used solely as a download list, so the serve venv stays the small Pi runtime.

Do not add those packages until the copy path exists. They would grow the bundle without changing what the task container can import.

### 4. Final summaries for rubric judges

Fourteen dev tasks are `rubric` and three are `checks-judge`. Where `final_message: true`, the judge reads the summary along with the files. The system note now asks for four things: the decision, the controlling numbers with units, the assumptions that could change the result, and the full path of each file. Keep the probe appendix short so it does not bury that summary. `solar-witness-test-package` scored 0 with a mid-thought sentence and no file; a summary of a partial package would still have given the judge something to grade.

### 5. The zero-score shapes, without task ids

| Shape | What to change in the harness |
|---|---|
| Died while computing, graded path empty | Prompt rule to write the path early. Probe reports it missing. Next: one repair turn that writes the zip from whatever is already in the work directory. |
| Stopped on 401/403 from a local app | Prompt rule to search the container for tokens and helper scripts (`/app/tools`, env files, app config) before stopping. Pi already proxies MCP; use it when the task lists `mcp_servers`, and still look on disk when the agent shells out to the app directly. |
| Generator script scored 0 (both MEP runs) | Repair turn runs the script, checks the IFC header, and if `ifcopenshell` imports, opens the file. Match classes and property-set names to an example IFC or a schema table in the task tree if one is there. Do not bake in rack counts, routes, or property-set names from the dev artifacts. |
| Finished zip under 0.4 | The repair checklist re-measures the limits the task text states (clearance, clash, headroom, required member names, demand/capacity). If one hard item fails, fix that item before chasing cost. A design that fails a hard check cannot score above 0.4 no matter how cheap it is. |

`data-center-site-model` is the positive control for IFC checks. When the next eval moves MEP off 0.0 into the 0.4 band, the hard gate is passing and further gain is the objective term. If it stays at 0.0, the script is still not producing a model the checker can score; look at the probe and the script's own stdout before touching routing heuristics.

## How to run locally once Vertex is available

This environment has no Docker daemon and no GCP credentials. `python -m kit validate` passes. `python -m kit check` passes `submission.yaml` and stops at `model` because `MODEL_PROXY_URL` and `MODEL_PROXY_KEY` are unset. Do not point those at a paid endpoint until you mean to spend.

On a machine with Docker, `uv`, and `gcloud`:

```bash
# competition kit, sibling of this repo
gcloud auth application-default login
export VERTEXAI_PROJECT=<gcp-project>
export MODEL_PROXY_KEY=$(openssl rand -hex 24)
kit/model_proxy/start.sh &          # http://localhost:4000, billed to VERTEXAI_PROJECT
export MODEL_PROXY_URL=http://localhost:4000

# Hugging Face: accept google/physical-engineerings-last-exam, then a read token
export HF_TOKEN=<hf-read-token>
uv tool install harbor==0.20.0 --with websockets

uv run python -m kit check ../submission-template
uv run python -m kit check ../submission-template --cancel-test   # optional

# one task first. This calls Claude Opus 5.5 and spends budget.
uv run python eval/run.py ../submission-template --env-file local.env \
  --tasks foundation-strategy

# the two MEP tasks, then the under-0.4 zips, then the full 29
uv run python eval/run.py ../submission-template --env-file local.env \
  --tasks data-hall-mep-routing,data-hall-mep-routing-offset

uv run python eval/run.py ../submission-template --env-file local.env
uv run python -m kit artifacts ../submission-template
```

`local.env` lives outside this repo (`MODEL_PROXY_URL`, `MODEL_PROXY_KEY`, `HF_TOKEN`). The judge for rubric tasks uses the same proxy unless `JUDGE_BASE_URL` is set. Leaderboard judging is Claude Opus 5.5; the kit asks the proxy for `claude-opus-5-5-judge` so the judge does not run at max reasoning.

Put `HF_TOKEN` and the proxy key only in that env file or the shell. This entry has no `.env` and must not grow one while the repo is public.

After a full run, `git add -A` so the new `artifacts/manifest.json` hashes the harness that produced it. A README-only edit is a note; a `harness.py` edit without a new run is the warning already seen here.

Set `name` in `submission.yaml` to the leaderboard slug you want before the run you submit. Renaming after the run changes the harness hash.

## What not to do

- Do not branch on task id, dev-set folder names, or the deliverable paths copied from `eval/dev_set.yaml`.
- Do not read `tests/`, grader scripts, or this repo's `artifacts/` from `serve.py` at runtime.
- Do not paste solutions from the published trajectories into the harness. Those runs scored 0.491 and the MEP scripts scored 0.
- Do not call any host other than the model endpoint. The serve container's egress proxy blocks the rest, and a 400 from a disallowed tool counts against the entry.
- Do not hand-edit `artifacts/` to hide the empty `foundation-strategy` folder. Re-run the task.

## Suggested order once credentials exist

1. `kit check` including smoke, on this commit, before any further harness edit.
2. Re-run `foundation-strategy` and `solar-witness-test-package`. Success is a non-empty graded file (and, for the witness package, a summary that states the decision). That tests the early-write prompt. The repair turn will not exist yet.
3. Re-run both MEP tasks. Compare reward to 0.0. If it is still 0, capture the script's stdout from the trial log before changing routing logic.
4. Implement the single repair turn and re-run the under-0.4 zip tasks (`roof-deck-design`, `wind-diaphragm-shear`, `seismic-diaphragm-shear`, `eor-review-corrections`, `division-26-specifications`, `mv-conveyance-study`, `data-hall-device-takeoff`).
5. Full 29-task `eval/run.py`, then commit artifacts with the harness. That commit is the one to submit. Entries close 5 January 2027, and a participant can have one submission queued or running at a time.
