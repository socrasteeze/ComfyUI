# Fork Maintenance

Everything needed to sync this fork from upstream and leave the installation
working. It is deliberately machine-independent: absolute paths, install
inventories, and host details stay in the untracked host notes named in
`.git/info/exclude`.

## Sync Contract

- Fetch upstream changes from `Comfy-Org/ComfyUI`, branch `master`.
- Publish only to this fork's `origin/main`. Never push to `upstream`; its push
  URL is deliberately set to a non-URL so an accidental push fails loudly.
- Track upstream master's tip, not the stable tag line. If the tip ever breaks
  the install, the fallback is the `release/vX.Y` maintenance branch, not a
  revert.
- Preserve upstream model, node, workflow, and API compatibility.
- Keep installation inventories and machine-specific handoffs local and
  untracked.
- Syncing the fork on the host does not update any installation by itself. Only
  a checkout or merge changes what runs.

## Sync Procedure

Merge, do not rebase. `git rebase upstream/master` refuses before doing any
work with `cannot rebase: You have unstaged changes`. The fork's own commits
are documentation-only, so a merge commit costs nothing.

### The symlink trap

Local `input`, `models`, and `output` may be directory symlinks pointing at
libraries outside the checkout. When they are, git reports every tracked
placeholder file under them as permanently deleted, and `git merge` also fails
before doing any work:

    error: 'input/example.png' is beyond a symbolic link
    fatal: stash failed

Git tries to stash the tree and cannot walk paths under a directory symlink.
This happens with no `merge.autoStash` configured anywhere, and also under
`--no-autostash`, so neither switch is the fix. Observed on git
2.52.0.windows.1.

Mark those placeholders `skip-worktree` for the duration of the merge:

    git fetch upstream
    git status --porcelain | grep '^ D ' | sed 's/^ D //' > paths.txt
    # Confirm paths.txt lists ONLY placeholders under input/, models/, output/
    git update-index --skip-worktree --stdin < paths.txt
    git merge upstream/master --no-edit
    git update-index --no-skip-worktree --stdin < paths.txt
    rm paths.txt

The `grep '^ D '` filter is required, not cosmetic: the redirection creates
`paths.txt` before `git status` runs, so an unfiltered list captures that file as a
39th entry and `git update-index` then fails on it. Check the count before applying.

`skip-worktree` is the right tool because it also stops git from writing those
paths out during the merge. Clear the flags in the same session; left set, they
hide real local changes from `git status`.

Never commit or restore the deleted placeholders, and never stash. Each of
those writes files through the symlinks into the real model and image
libraries.

### After the merge

1. Confirm the deletion baseline is back, with nothing else modified or
   untracked. The untracked host notes record the expected count for this
   installation.
2. Reinstall `requirements.txt` if the merge touched it. See below.
3. Run the GPU acceleration check. See below.
4. Push `main` to `origin` only.

A non-zero result from step 2 or 3 is a failed sync. Report it; do not treat
the merge as clean because git succeeded.

## Environment Constraints

These hold for any installation this fork is checked out into. All of them fail
silently, so each one needs its own check after any pip operation.

### Dependency pins

After a merge that moves `requirements.txt`, reinstall it:

    python -m pip install -r requirements.txt

Skipping this is a hard crash, not a degraded mode. Core code calls symbols that
exist only in the newly pinned versions, and the traceback names a core module
rather than the stale package, so it reads as upstream breakage.

Omit `-U`. Unpinned dependencies must be left alone: the installation runs a
torch build matched to an attention wheel compiled against that exact pair, and
upgrading torch breaks attention. When installing bumped pins by hand instead,
run `pip install --dry-run` first and confirm torch and torchvision are absent
from the "Would install" line.

### ONNX Runtime must stay GPU-only

Installations that use DWPose, WD14 tagging, or any other ONNX node run
`onnxruntime-gpu`. Never install plain `onnxruntime` beside it. Both packages
write the same `capi/onnxruntime_pybind11_state.pyd` and the last one installed
wins; a CPU build that overwrites the GPU one raises no error. The provider list
just empties and every ONNX node falls back to CPU.

Any pip operation can cause this, including a custom node's own
`requirements.txt`. ComfyUI-RMBG lists both packages; the CPU line is commented
out locally and must stay commented after any node update.

Confirm which distribution owns the binaries:

    python -c "import onnxruntime.capi.build_and_package_info as i; print(i.package_name)"

It must print `onnxruntime-gpu`. Do not repair a failure by installing
`onnxruntime`. That is the original defect, not the fix.

Two further pieces hold this together, and both live outside the checkout:

- A cuDNN version pin. The `onnxruntime-gpu[cuda,cudnn]` extras pull a cuDNN too
  new for the installed ORT frontend, which then fails at
  `build_operation_graph` with `CUDNN_BACKEND_API_FAILED` on any Conv node. Do
  not let cuDNN upgrade.
- A `.pth` in site-packages that puts the nvidia wheel `bin` directories on
  `PATH` at interpreter start. ORT loads its provider DLL with plain
  `LoadLibrary`, which ignores `os.add_dll_directory`, so a `.pth` using
  `add_dll_directory` does not work and `PATH` does. The same file is also what
  lets `llama_cpp` find its CUDA dependencies, so it is not only an ORT
  workaround. Do not delete it.

### Verifying acceleration

Provider enumeration is not a test. `get_available_providers()` succeeds even
when the provider DLLs cannot load. Import torch first, then build a real
`InferenceSession(..., providers=["CUDAExecutionProvider"])` over a small Conv
model and confirm `get_providers()` still lists CUDA.

A healthy startup logs `DWPose: Onnxruntime with acceleration providers
detected`. The degraded line reads `Onnxruntime not found or doesn't come with
acceleration providers`.

The host keeps a script that performs exactly this check and exits non-zero when
degraded. It is machine-local and untracked because it hard-codes interpreter
paths; the untracked host notes name it.

## Local Fixes

- Classify `.m2v` as video explicitly; it is absent from some system MIME tables.
- Use a native absolute temporary home path in the extra-config test fixture.
  A root-relative Unix path is not an absolute Windows home path.
- Use a relative special-token map path in the Hunyuan DiT tokenizer config.
  Keep the upstream developer's home path out of published configuration.

## Fork tooling

`fork_tools/` is fork-only and never exists upstream, so it cannot conflict on a
sync. `fork_tools/prompt_guides/` holds per-image-model prompt-writer system
prompts, a `profiles-noninteractive/` variant for unattended use inside a
workflow, a harness that dry-runs them against `VALIDATION_CASES.md` on any
OpenAI-compatible or Ollama server, and the graded results. The harness reads
the server from `PROMPT_GUIDES_OLLAMA` and defaults to loopback; no host
details are stored in the tree.

## Verification

Use the repository's CI commands. Portable Python can hard-code the live
checkout in its `._pth` file; verify `folder_paths.__file__` before testing a
worktree. Test child processes must resolve the same isolated Python and
checkout. A test server connecting to an existing live server is not a valid
execution baseline.

A portable install has no pytest, and installing one into it risks the ONNX
Runtime stack described above. When the full suite is not available, validate
merged source with `python -m py_compile` over the changed files plus an import
of any changed `comfy_extras.*` module.

Keep custom nodes, models, user databases, and test output outside the
verification checkout's published changes. Record baseline failures by test name
and cause.

## Sync Log

- 2026-09-12 (eighteenth sync): Adopted four upstream commits, `9113c08c` through
  `7ba217d6`. `9113c08c` consumes server estimated-duration headers for partner-node
  progress, removes the inert synchronous-operation estimate parameter, and hardens polling
  against interrupts and extractor failures. `7dac1d25` raises Yue2's advertised maximum
  song duration from 360 to 900 seconds while limiting generation to the remaining model
  context. `7ba217d6` keeps the alpha channel unchanged in Image Add Noise and adds five unit
  tests. A final pre-push refresh found `a20738f1`, which makes `linear_input_act` honor the
  `_full_precision_mm` fallback for tensor-wise INT8 weights and adds a focused regression
  test. All four were adopted as-is. Nothing matches a rejected-feature pattern. Both merges
  used `ort` with zero conflicts. All three fork touchpoints remained intact: the `.m2v` MIME
  entry, the Windows absolute temporary-home fixture, and the Hunyuan DiT tokenizer's relative
  `special_tokens_map_file` path. Local `main` first fast-forwarded four commits to current
  `origin/main` (`f30cdc9b`), including the seventeenth sync. The host then installed the pending
  `comfyui-frontend-package` 1.52.7 pin after a dry-run showed no Torch or torchvision change.
  The upstream merge protected exactly 38 symlink placeholder deletions with direct-argument
  `skip-worktree`; all flags were cleared and the 38-deletion/zero-other-change baseline was
  restored. `requirements.txt` did not change in this upstream window. Gates: all 841 tracked
  Python files byte-compiled before and after the merge; Ruff reported the same eight
  pre-existing fork-harness `T201` findings, while all ten changed Python files passed Ruff;
  eight changed modules imported; the five new alpha tests and the focused mixed-precision
  regression test passed through direct invocation;
  and the isolated CPU quick-start passed with an in-memory database, custom nodes disabled,
  and API nodes disabled. Both host installations still use `onnxruntime-gpu`, and real Conv
  inference passed on `CUDAExecutionProvider`. Pytest and Pylint remain unavailable in the
  portable runtime and were not installed. Merge base `c75d8c96`.
- 2026-09-12 (seventeenth sync): Adopted two upstream commits, `c75d8c96` and `7193f562`.
  `c75d8c96` adds Bria partner-node image-edit nodes and a Video Eraser node: a new
  `comfy_api_nodes/apis/bria.py` (145 lines) plus a large extension of
  `comfy_api_nodes/nodes_bria.py` (+766/-8). `7193f562` bumps `requirements.txt`'s
  `comfyui-frontend-package` pin from `1.51.10` to `1.52.7`. Both adopted as-is; nothing in
  this window matches a rejected-feature pattern. Zero conflicts (merge strategy `ort`); none
  of the three existing fork touchpoints (`folder_paths.py`'s `m2v` MIME entry,
  `tests-unit/utils/extra_config_test.py`'s absolute-tmp-home fixture, the Hunyuan DiT
  tokenizer config's relative `special_tokens_map_file` path) is in this window, and all three
  were verified intact and untouched afterward. This sync ran in a disposable Linux container:
  `input`/`models`/`output` are plain directories, not symlinks, so the symlink-trap workaround
  did not apply. `requirements.txt` changed (frontend package version only, no torch/runtime
  pin touched), consistent with prior dependency-less-session entries this reinstall could not
  be exercised. Gates: a full-tree byte-compile of all tracked `.py` files via `py_compile`
  (individually) is clean, 0 errors; the two new/changed Bria files compile individually too.
  `ruff check .` reports the same 8 pre-existing `T201` (bare `print`) findings as the sixteenth
  sync, all in `fork_tools/prompt_guides/harness/{dryrun,grade,patch_profiles}.py`, none touched
  by this window. Author/committer scan on the merge range showed only
  `socrasteeze <socradeez@gmail.com>` (merge) and the two upstream authors, preserved. Local
  `main` was already level with `origin/main` (identical tip, `6378dd91`) at session start, so
  the incoming window was exactly these two commits. Merge commit `eb34a17f`; merge base
  `b058ec65` (the tip of the sixteenth sync). **Not covered:** no live GPU/CUDA inference, no
  ONNX Runtime check, no pytest run (no test dependencies installed in this container), no
  actual `pip install -r requirements.txt` for the frontend-package bump — those still need a
  pass on an actual installation per the standing procedure.
- 2026-09-12 (sixteenth sync): Adopted four upstream commits, `d537de93` through `b058ec65`:
  `d537de93` implements a Video Concatenate node (`comfy_extras/nodes_video.py`) plus a large
  extension of `comfy_api/latest/_input_impl/video_types.py` to support accumulating multiple
  video inputs, with a new `tests-unit/comfy_api_test/video_accumulation_test.py` (288 lines).
  `c40c94e1` immediately fixes that new test file (+5/-3). `1d91a82d` adds Marigold v2 support
  (CORE-431): a new `comfy_extras/nodes_marigold.py` post-process node (depth/normals/albedo
  from a decoded prediction), a `model_sampling.py` addition, and new conditioning helpers in
  `nodes_cond.py`, registered via `nodes.py`'s extra-node list. `b058ec65` adds the Yue2 music
  model: two new audio encoders (`comfy/audio_encoders/mert2.py`, `sheetsage2.py` +
  `sheetsage2_abc.py`), a new `comfy/ldm/yue2/model.py` and `comfy/text_encoders/yue2.py`,
  `supported_models.py`/`model_detection.py`/`latent_formats.py`/`sd.py` entries, and a `yue2`
  option added to `CLIPLoader`'s `type` combo in `nodes.py`. 24 files changed, +3085/-32 (two
  files, `nodes.py` and `tests-unit/comfy_api_test/video_accumulation_test.py`, are touched by
  more than one commit in the window, which is why the file count is lower than the sum of the
  four commits' individual stats). All four adopted as-is; nothing in this window matches a
  rejected-feature pattern. Zero conflicts; none of the three existing fork touchpoints
  (`folder_paths.py`'s `m2v` MIME entry, `tests-unit/utils/extra_config_test.py`'s
  absolute-tmp-home fixture, the Hunyuan DiT tokenizer config's relative `special_tokens_map_file`
  path) is in this window, and all three were verified intact and untouched afterward. This
  sync ran in a disposable Linux container: `input`/`models`/`output` are plain directories, not
  symlinks, so the symlink-trap workaround did not apply (`git status --porcelain | grep '^ D '`
  found zero placeholders, before and after). `requirements.txt` did not change, so no
  reinstall. Gates: a full-tree byte-compile of all 840 tracked `.py` files via `py_compile`
  (individually, not just `compileall`) is clean, 0 errors; the eight new/changed files from
  this window compile individually too. `ruff check .` reports 8 pre-existing `T201` (bare
  `print`) findings, all in `fork_tools/prompt_guides/harness/{dryrun,grade,patch_profiles}.py`
  — fork-only CLI harness scripts whose job is to print progress/results to a terminal; none of
  those three files is touched by this window's diff (confirmed via `git diff --name-only` over
  the merge range) or by any prior sync, so this is a standing condition to note, not a
  regression to chase down here. This container has no GPU and no installed dependencies (no
  torch), consistent with every other dependency-less-session entry in this log, so the
  GPU acceleration check and a real import of the new torch-dependent modules
  (`comfy_extras.nodes_yue2`, `nodes_marigold`, `comfy.audio_encoders.*`) could not run — noted
  rather than skipped silently. Author/committer scan on the merge range showed only
  `socrasteeze <socradeez@gmail.com>` (merge) and the four upstream authors, preserved. Local
  `main` was 43 commits behind `origin/main` at session start (all already-published prior
  syncs, none of them a divergence this session needed to redo) and was fast-forwarded to
  `origin/main`'s tip (`36ca99e2`) before fetching upstream; from there the incoming window was
  exactly these four commits. Merge commit `103f34ab`; merge base `1d48d9cf` (the tip of the
  fifteenth sync, confirming the fork was level with its own last sync before this one began).
  **Not covered:** no live GPU/CUDA inference, no ONNX Runtime check, no pytest run (no test
  dependencies installed in this container) — those still need a pass on an actual installation
  per the standing procedure.
- 2026-09-11 (fifteenth sync): Adopted one upstream commit. `1d48d9cf` adds a `linear` option to
  the `ImageColorSpace` node's source/destination combos (`comfy_extras/nodes_images.py` +7/-3):
  linear input skips the sRGB EOTF before the Rec.709->Rec.2020 primary conversion, and linear
  output skips the SDR tone-map/gamut-compress after converting back, both anchored to the same
  203-nit reference white as sRGB. Zero conflicts; not a fork touchpoint (file untouched by the
  fork relative to the merge base). Merge is `f2a9b729`; merge base `6338e4bd`, the tip of the
  fourteenth sync, so the window was exactly this one commit. Gates: `python3 -m py_compile`
  clean on the changed file; no fork symbol references `ImageColorSpace` so no sweep needed.
- 2026-09-10 (fourteenth sync): Adopted three upstream commits. `5774ab9c` adds auto aspect ratio to
  the OpenRouter MAI image partner node (`comfy_api_nodes/nodes_openrouter.py` +17/-6). `6338e4bd`
  fixes the H3 fun ControlNet under the comfy compiler (`comfy_extras/nodes_minimax_h3.py` +8/-3).
  `1f641fd9` bumps `comfyui-workflow-templates` 0.11.57 -> 0.11.59. Zero conflicts; none of the three
  touches a fork touchpoint. Merged with the skip-worktree sequence over the 38 placeholder deletions,
  flags cleared afterwards, baseline back at 38 with nothing else modified. The pin moved, so
  `requirements.txt` was reinstalled into `python_embeded` (dry-run first: only the templates package and
  its three sub-packages, no torch or torchvision). Gates: `onnxruntime-gpu` owns the binaries,
  torch 2.9.1+cu130 sees the RTX 5090, and `check-gpu-accel.bat` reports ALL INSTALLS OK. Note the
  `python` on PATH is a system Python 3.12, not this install: a dry-run against it wanted 40+ packages.
- 2026-09-10 (thirteenth sync): Adopted two upstream commits. `6eba895f` migrates the Tripo
  partner nodes to Tripo's v3 API, adds the Smart Segment node, and retires the dead widgets
  on the old Text to Model / Image to Model / Texture Model nodes in favor of their V2
  replacements (`comfy_api_nodes/apis/tripo.py` +/-150, `comfy_api_nodes/nodes_tripo.py`
  +921/-697 combined). `a7b1d39d` is a `README.md`-only update to the manual Windows AMD
  install instructions. Zero conflicts; neither commit touches any of the three existing
  fork touchpoints (`folder_paths.py`, the Hunyuan DiT tokenizer config,
  `tests-unit/utils/extra_config_test.py`), which were verified intact and unmodified by this
  window. This sync ran in the same disposable Linux container as the twelfth sync: no
  symlinked `input`/`models`/`output` so the symlink trap did not apply, and no GPU, ComfyUI
  custom node ecosystem, or `requirements.txt` change to reinstall in this window. There is no
  `tests-unit` coverage for the Tripo nodes. The container has no `pydantic` (or the rest of
  the runtime dependency stack), so a real import of `comfy_api_nodes.apis.tripo` was not
  possible; verified instead with `python -m py_compile` on both changed files, an `ast.parse`
  of each, and a full-tree `python -m compileall` (all clean). Author/committer scan on the
  merge range showed only `socrasteeze <socradeez@gmail.com>` (merge) and the two upstream
  authors, preserved. **Not covered:** no live Tripo API smoke test (needs a key and network
  this container doesn't have), no real ONNX/CUDA inference, no host-install verification —
  those still need a pass on the actual machines per the standing procedure.
- 2026-09-10 (twelfth sync): Adopted one upstream commit, `7ea14e59`: added a "Gemini 3.8
  Flash" option to the Gemini text node's model `DynamicCombo` (`comfy_api_nodes/nodes_gemini.py`,
  +41/-24), refactoring the shared per-model input builder to make the temperature/top_p
  sampling inputs optional (the new model omits them) rather than adding a parallel code
  path. Zero conflicts; `nodes_gemini.py` is not a fork touchpoint and none of the three
  existing fork touchpoints (`folder_paths.py`, the Hunyuan DiT tokenizer config,
  `tests-unit/utils/extra_config_test.py`) were touched by this window. This sync ran in a
  disposable Linux container rather than either host install: no symlinked `input`/`models`/
  `output` here so the symlink trap did not apply, and there is no GPU, no ComfyUI custom
  node ecosystem, and no `requirements.txt` changes to reinstall in this window regardless.
  The changed file byte-compiled cleanly; author/committer scan on the merge range showed
  only `socrasteeze <socradeez@gmail.com>` (merge) and the upstream author, preserved.
  **Not covered:** no live Gemini API smoke test (needs a key and network this container
  doesn't have), no real ONNX/CUDA inference, no host-install verification — those still need
  a pass on the actual machines per the standing procedure.
- 2026-09-09 (eleventh sync): Reconciled the local checkout with the three already-published
  syncs through `edb5e321`, then adopted `4989cdd9` and `be923968` as-is: OpenRouter
  MAI-Image-2.6 image nodes and provider-error details, a string-validation message fix,
  and removal of the dead ROCm Triton architecture gate. The new upstream window changes
  six files, +307/-36. No conflicts or orphaned references to the removed gate remained.
  Both existing fork fixes remain intact. All 38 symlink placeholders were protected
  during the merges, and all temporary index flags were cleared immediately afterward.
  Origin reconciliation required workflow templates 0.11.55 to 0.11.57; the requirements
  dry run and install changed only template packages. Torch and the GPU-only ONNX Runtime
  remained unchanged. Baseline and post-merge checks passed: 829 tracked Python files
  byte-compiled, Ruff passed, core startup passed with isolated temporary state and custom
  and API nodes disabled, and real ONNX CUDA inference passed on both host installations.
  Nine changed modules imported. Local checks covered 3D saved outputs, legacy preview
  output, OpenRouter registration, image decoding and provider errors, and all 111 blueprint
  JSON files. Pytest and Pylint were unavailable; no test dependencies were installed in
  the portable runtime. The delivery scrub replaced an old absolute home path in the
  Hunyuan DiT tokenizer config with a relative path; local tokenization was unchanged.
  The upstream path remains in existing history, with no credential rotation or rewrite
  needed. Other scan matches were legitimate model content, CI checks, or test fixtures.

- 2026-09-09 (tenth sync): Adopted one upstream commit, `6f3895ed` ("main: bump the AMD
  Windows VA quota to 4TB", #16199): raises `main.py`'s ROCm `OCL_SET_SVM_SIZE` env var from
  `262144` (256KB, the AMD-requested value from a prior upstream commit) to `4194304` (4TB),
  bringing AMD's Windows GPU virtual-memory quota in line with the other platforms' headroom.
  1 file, +1/-1. Clean merge, zero conflict markers; the symlink trap did not apply
  (`input`/`models`/`output` are absent in this container, not symlinks). Neither fork-local
  fix (`folder_paths.py`'s `m2v` MIME entry, `tests-unit/utils/extra_config_test.py`'s
  absolute-tmp-home fixture) is in this window; both verified intact and untouched —
  `requirements.txt` did not change, so no reinstall flag this time. Validation: this
  session has no GPU and no installed dependencies (no torch, no numpy), consistent with
  every other dependency-less-session entry in this log — `python -m py_compile` on
  `main.py` and a full-tree sweep over all tracked `.py` files are both clean (0 errors),
  and `ruff check .` reports "All checks passed!" (the same pre-existing
  `sam3/detector.py:12` `# noqa` warning as prior syncs, on an untouched file outside this
  window's diff). Merge commit is the tip of `origin/main` after this sync.

- 2026-09-09 (ninth sync): Adopted six upstream commits, `be47aa22` through `54e03f53`:
  `be47aa22` ([Partner Nodes] add GPT Image 2.5 Flare and Sunburst models to the OpenAI node,
  #16190), `02dfb63b` (chores: update tooltips of 3D nodes, CORE-323, #16179), `6517734f`
  (chore: update workflow templates to v0.11.57, #16192), `3074d0e3` (report the file saved
  by Save 3D (Advanced) as a standard 3d output item, #16171, plus its new unit test),
  `40c4fcdf` (ComfyUI v0.35.0 version bump), and `54e03f53` (add new model blueprints and
  reorganize subgraph categories, #14785 — the bulk of the diff: ~30 new `blueprints/*.json`
  workflow files plus edits to existing ones). All adopted as-is; nothing in this window
  matches a rejected-feature pattern. 87 files changed, +59584/-372 (the blueprint JSON
  additions dominate the line count). Clean merge, zero conflict markers; the symlink trap
  did not apply (`input`/`models`/`output` are absent in this container, not symlinks).
  Neither fork-local fix (`folder_paths.py`'s `m2v` MIME entry,
  `tests-unit/utils/extra_config_test.py`'s absolute-tmp-home fixture) is in this window;
  both verified intact and untouched. `requirements.txt` changed (2 lines) — flagging for
  reinstall on the next real installation; this session has no installed dependencies to
  reinstall against. Validation: this session has no GPU and no installed dependencies (no
  torch, no numpy), consistent with every other dependency-less-session entry in this log —
  a full-tree `python -m py_compile` over all 829 tracked `.py` files is clean (0 errors),
  and `ruff check .` reports "All checks passed!" (the same pre-existing
  `sam3/detector.py:12` `# noqa` warning as prior syncs, on an untouched file outside this
  window's diff). The GPU acceleration check and the new `nodes_load_3d`/`nodes_save_3d`/
  `nodes_openai` import checks could not run (`ModuleNotFoundError` for `torch`/`numpy`) —
  noted rather than skipped silently, per this log's own standard. Merge commit `5d60520c`.

- 2026-09-09 (eighth sync): Adopted one upstream commit, `672ba9e5` ("Only lock repo PRs
  after merging if they contain a CLA signature.", #16191): a CLA-bot workflow change to
  `.github/workflows/cla.yml` only, gating the allowlist/CLA-assistant steps on
  `pull_request_target` events that are not a close, and adding a `lock-pullrequest-aftermerge:
  false` input plus a new post-merge step that locks a merged PR itself once a CLA signature
  or bot approval comment is found on it. 1 file, +27/-3. Clean merge, zero conflict markers;
  the symlink trap did not apply (`input`/`models`/`output` are absent in this container, not
  symlinks). Neither fork-local fix (`folder_paths.py`'s `m2v` MIME entry,
  `tests-unit/utils/extra_config_test.py`'s absolute-tmp-home fixture) is in this window;
  both verified intact and untouched. `requirements.txt` untouched, no reinstall needed.
  Validation: this session has no GPU and no installed dependencies (no torch), consistent
  with every other dependency-less-session entry in this log — a full-tree `python -m
  py_compile` over all 829 tracked `.py` files is clean (0 errors), and `ruff check .`
  reports "All checks passed!" (the same pre-existing `sam3/detector.py:12` `# noqa` warning
  as prior syncs, on an untouched file outside this window's diff). The GPU acceleration
  check could not run (no GPU, no `nvidia-smi`, no torch) — noted rather than skipped
  silently. Merge commit `9787404`; pre-merge fork HEAD was `cfd8be3`.
- 2026-09-08 (seventh sync): Reconciled local `main` with the already-published sixth sync,
  then adopted five upstream commits, `488e8f8a` through `421a1c24`: Pixal3D multiview
  support, two quantized text-encoder matrix-multiply fixes including Gemma4 prefill cache
  positions, a new LTXV pre-encoded latent-guide node, and a MiniMax H3 denoise-mask fix.
  11 files, +728/-147. All five commits were adopted as-is. None touches either fork-local
  fix. The merge used the documented symlink procedure with all 38 placeholders protected;
  the flags were cleared in the same operation and the 38-deletion baseline returned with no
  other visible file. Zero unmerged paths and zero exact conflict markers remained. The
  earlier origin reconciliation moved three package pins (`comfyui-frontend-package` 1.51.9
  to 1.51.10, `comfyui-embedded-docs` 0.5.10 to 0.5.11, and `comfy-aimdo` 0.5.2 to 0.5.3):
  a dry run showed only those packages would install, the live install was updated without
  changing torch or torchvision, and the mandatory GPU check passed afterward. The remaining
  five-commit window did not touch `requirements.txt`. Pre-merge and post-merge fallback gates
  were green: all tracked Python files byte-compiled (827 before, 829 after), Ruff passed,
  and the changed `comfy_extras.nodes_lt` and `comfy_extras.nodes_trellis2` modules imported
  against the live torch environment. The `.m2v` MIME entry and native Windows temporary-home
  fixture remain intact. The GPU acceleration check passed post-merge on both installations
  (`ALL INSTALLS OK`). `pytest` and Pylint remain unavailable in the portable environment;
  they were not installed because the documented dependency policy forbids risking the
  GPU-only ONNX Runtime stack.
- 2026-09-08 (sixth sync): Adopted one upstream commit, `00d34d9` ("Comfy Aimdo 0.5.3 +
  Memory compiler fixes", #16180): a `comfy-aimdo` pin bump from 0.5.2 to 0.5.3 plus memory
  compiler fixes across `comfy/model_prefetch.py`, `comfy/multigpu.py`, `comfy/sd.py`, and
  small dtype/device touch-ups in `comfy/latent_formats.py`,
  `comfy/ldm/lightricks/av_model.py`, `comfy/ldm/minimax/model.py`,
  `comfy/ldm/minimax_music/ar.py`, `comfy/model_management.py`,
  `comfy/text_encoders/llama.py`, `comfy_extras/nodes_sparse_attention.py`, and
  `latent_preview.py`, plus a new `tests-unit/execution_test/preview_compiler_test.py`.
  13 files, +153/-59. Clean merge, zero conflict markers anywhere in the tree; the symlink
  trap did not apply (`input`/`models`/`output` are plain directories in this container, not
  symlinks — `git status --porcelain | grep '^ D '` found zero placeholders). Both fork-local
  fixes (`folder_paths.py`'s `m2v` MIME entry, `tests-unit/utils/extra_config_test.py`'s
  absolute-tmp-home fixture) verified intact and untouched — neither file is in this window.
  `requirements.txt` moved one pin (`comfy-aimdo` 0.5.2→0.5.3); a scoped
  `pip install --dry-run comfy-aimdo==0.5.3` shows only that package under "Would install",
  confirming no other packages (torch/torchvision included) are pulled in by the bump.
  Validation: this session has no GPU and no installed dependencies (no torch, numpy, or
  comfy_kitchen), consistent with every other dependency-less-session entry in this log — a
  full-tree `python -m py_compile` over every tracked `.py` file is clean (0 errors), and
  `ruff check .` reports "All checks passed!" (the same pre-existing `sam3/detector.py:12`
  `# noqa` warning as prior syncs, on an untouched file outside this window's diff). The GPU
  acceleration check could not run at all (no GPU, no `nvidia-smi`, no torch) — noted rather
  than skipped silently, per this log's own standard. Merge commit `3dc4aaf`; pre-merge fork
  HEAD was `b1db5cd`.
- 2026-09-07 (fifth sync): Reconciles with the 2026-09-08 entry below, which was pushed to
  `origin/main` from a dependency-less container while this session's merge was in flight, and
  adds the one upstream commit that entry did not reach. This session merged all three commits
  then new on `upstream/master` -- `f5ed117b`, `5bbdf8a7`, and `efa6c8f8` -- as merge commit
  `ff02a854` off `61adeb96`; the push was then rejected because that other session had already
  landed the first two as `71e01d1d`. Merging `origin/main` back in left `efa6c8f8` as the only
  net-new content here: it adds the LTXV generated-keyframe nodes plus Freeze Latent as a new
  `comfy_extras/nodes_lt_keyframes.py` (1051 lines) with a 911-line test module, registered by
  one added line in `nodes.py`. The only merge conflict in either direction was this file's log
  section, resolved by keeping the 2026-09-08 entry verbatim and rewriting this one around it;
  zero conflict markers in the tree, both merges done via the skip-worktree procedure above (38
  placeholders flagged and cleared each time), deletion baseline restored to 38 with nothing
  else modified or untracked. No fork touchpoint in any of the three commits, and both
  fork-local fixes (`folder_paths.py` `m2v`, `extra_config_test.py` fixture) verified intact.
  `requirements.txt` unchanged, so no reinstall. Validation ran on the live install rather than
  a bare container, so it also covers the two commits the entry below could only byte-compile:
  all six changed files byte-compiled clean, and `nodes_lt_keyframes`, `nodes_model_advanced`,
  and `nodes_sparse_attention` all imported against real torch. `nodes_lt_keyframes` and
  `nodes_sparse_attention` report empty `NODE_CLASS_MAPPINGS` by design (they register through
  the `comfy_entrypoint` extension API); `nodes_model_advanced` keeps its legacy mapping and
  still exposes `ModelAttentionBackend` there, now as an `io.ComfyNode`, so `5bbdf8a7`'s
  rewrite does not drop a node. The GPU acceleration check passed on both installs
  (`ALL INSTALLS OK`, exit 0) -- the check the entry below records as unrunnable.
- 2026-09-08: First reconciled two stranded prior syncs, then adopted two new upstream
  commits. The session branch `claude/tender-noether-ykvwnh` held 29 commits (including
  the 2026-09-07 fourth-sync merge and its log entry) that a previous session never
  fast-forwarded onto `main`; `git merge --ff-only` from `main` onto that branch tip
  (`271e44b0` to `61adeb96`) applied cleanly with no divergence to reconcile. From there,
  `git fetch upstream` (adding the `upstream` remote fresh in this checkout, push URL set
  to `DISABLED` and verified before any other remote operation) found two new upstream
  commits: `5bbdf8a7` ("Harmonize model attention nodes", #16154), which reworks
  `nodes_model_advanced.py`'s and `nodes_sparse_attention.py`'s attention-node wiring, and
  `f5ed117b` ("Remove useless code", #16169), a 7-line dead-code removal in
  `comfy/ldm/cosmos/predict2.py`. Neither commit touches a fork-local file. Clean merge via
  `git merge upstream/master --no-edit`, zero conflict markers anywhere in the tree; the
  symlink-trap workaround was checked and not needed (`input`/`models`/`output` are plain
  directories in this container, not symlinks — `git status --porcelain | grep '^ D '`
  found zero placeholders). Both fork-local fixes (`folder_paths.py`'s `m2v` MIME entry,
  `extra_config_test.py`'s absolute-tmp-home fixture) verified intact and untouched.
  `requirements.txt` unchanged, so no reinstall. Validation: this session has no GPU and no
  installed dependencies (no torch, numpy, or comfy_kitchen), consistent with every other
  dependency-less-session entry in this log — a full-tree `python -m py_compile` over every
  tracked `.py` file is clean (0 errors), and the three merge-touched files
  (`comfy_extras/nodes_model_advanced.py`, `comfy_extras/nodes_sparse_attention.py`,
  `comfy/ldm/cosmos/predict2.py`) byte-compile clean individually too; attempted imports of
  those modules fail only on the missing `torch`/`comfy_kitchen` dependencies, not on any
  merge defect. The GPU acceleration check could not run at all (no GPU, no `nvidia-smi`,
  no torch) — noted rather than skipped silently, per this log's own standard. Merge commit
  `71e01d1d`; pre-merge (post-fast-forward) fork HEAD was `61adeb96`.
- 2026-09-07 (fourth sync): Adopted three upstream commits through `41db8f4f`:
  `313a76fb` disables int8 weight-only quantization on devices lacking `torch._int_mm`
  (an MPS crash fix; touches `comfy/ops.py`, `comfy/controlnet.py`, `comfy/model_management.py`,
  `comfy_extras/nodes_model_patch.py`, plus a new `test_mixed_precision.py`), `9ac7352f` fixes
  node registration issues in `nodes.py`/`main.py` (adds `main_prestartup_test.py` and
  `test_ignore_display_name.py`), and `41db8f4f` verifies aotriton kernels actually launch
  before enabling pytorch attention in `model_management.py`. Nine files, +258/-15; clean
  merge via the skip-worktree procedure above (38 placeholders flagged and cleared), zero
  conflict markers, deletion baseline restored to 38 with nothing else modified or untracked.
  Both fork-local fixes (`folder_paths.py` `m2v`, `extra_config_test.py` fixture) verified
  intact. `requirements.txt` unchanged, so no reinstall. Validation on the live install: all
  nine changed files byte-compiled clean, `comfy_extras.nodes_model_patch` imported, and the
  GPU acceleration check passed on both installs (`ALL INSTALLS OK`, exit 0). Merge commit
  `7b22e580`; pre-merge fork HEAD was `f7f6bfd0`.
- 2026-09-07 (third sync): Adopted one upstream commit, `eb357862`, a lone
  `comfyui-frontend-package` pin bump from 1.51.9 to 1.51.10 (#16118). No source changed.
  Clean merge, zero conflict markers anywhere in the tree; both fork-local fixes
  (`folder_paths.py`'s `m2v` MIME entry, `extra_config_test.py`'s absolute-tmp-home fixture)
  verified intact and untouched. Validation: this session has no GPU runtime and no installed
  dependencies (fresh scratch clone — no torch, no numpy, no pytest deps), so the full
  reinstall, GPU acceleration check, and pytest suites are unrun, consistent with every other
  dependency-less-session entry in this log. In place of that: a full-tree `python -m
  py_compile` over all 822 tracked `.py` files, run before and after the merge, is clean both
  times (0 errors, byte-identical empty output); `ruff check .` reports "All checks passed!"
  both times too (one incidental `# noqa`-syntax warning on an untouched file,
  `comfy/ldm/sam3/detector.py:12`, appeared on the pre-merge run and not the post-merge one on
  a rerun with no tree change in between — a ruff-side flake, not a merge effect, since that
  file is outside this window's diff). A scoped `pip install --dry-run
  comfyui-frontend-package==1.51.10` shows only that package under "Would install", confirming
  no other packages (torch/torchvision included) are pulled in by the bump. This session's
  starting branch (`claude/tender-noether-z02bsu`) was found already fully merged into
  `origin/main` (identical tip, zero divergence) before this sync began, so it was reset to
  `origin/main` and this sync's two commits (merge + this entry) were built on top of that,
  then pushed back to `origin/main`. Merge base `eb357862`'s parent, i.e. `ea33b154` (the tip
  of this morning's second sync).
- 2026-09-07 (second sync): Adopted one upstream commit, `ea33b154`, a Porter-Duff alpha-blend
  fix for compositing (#15721): `nodes_compositing.py`'s blend modes now composite the RGB
  channels using the correct source/destination alpha weighting instead of blending alpha into
  the result unconditionally, and a new `nodes_compositing_test.py` pins the corrected output
  for `normal`, `multiply`, and `screen` against a partially-transparent source. Two files,
  +66/-6; clean merge, zero conflict markers anywhere in the tree, no fork touchpoint (neither
  file carries prior fork edits — `nodes_compositing.py` has never been in this fork's
  divergence list). `requirements.txt` unchanged, so no reinstall. Validation: this session has
  no GPU runtime and no installed dependencies (fresh scratch clone — no torch, no numpy, no
  pytest), so the full reinstall, GPU acceleration check, and pytest suite are unrun, consistent
  with every other dependency-less-session entry in this log; both changed files byte-compiled
  clean with `py_compile`, which is what stands in for the import/test check per that same
  pattern. Merge commit `b346d39c`; merge base `ea33b154`'s parent (the tip of this morning's
  sync); pre-merge fork HEAD was `d4815c4` (this morning's sync commit).
- 2026-09-07: Adopted thirteen upstream commits through `fbed745c`: a batch of alpha-channel
  correctness fixes across the image nodes (Invert Image `fbed745c`, Blend Images `f9c706f3`,
  Draw Text Overlay `20f1a412`, Quantize Image `aa4582f9`, the color adjustment nodes
  `25dfc16f`, Detect Edges/Canny `d03a2430`, RGB/YUV conversion `07dd46dc` — these previously
  inverted, blended, or otherwise mutated the alpha channel where they should have left it
  alone), a new color space conversion node (`7b3b262b`), a test-isolation fix for a leaked
  `cli_args` singleton (`82db4037`, rewrites `tests-unit/comfy_test/folder_path_test.py` to use
  `monkeypatch` instead of `sys.argv` patching), a comfy-compiler change pausing it for
  long-lived sparse allocations (`a99d1f9c`), and three commits already reviewed and staged on
  a stray branch from an earlier session (`15eb748b` embedded-docs 0.5.10→0.5.11,
  `e308cc73` Sparse Attention node, `d1c5e641` an mps `supports_fp64(None)` guard) that had
  never reached `origin/main` — that branch (`claude/tender-noether-v202mp`) held a real
  completed merge (`ab02f366`) plus its log entry, stranded off-branch; this sync supersedes it
  by merging upstream directly into `main`, so those three commits are adopted here instead.
  The fork owner should delete the stray branch once this lands, since its content is now
  fully subsumed by `main`. 21 files changed, 20 python + this file; clean merge, zero conflict
  markers anywhere in the tree. Both fork-local fixes (`folder_paths.py`'s `m2v` MIME entry,
  `extra_config_test.py`'s absolute-tmp-home fixture) verified intact and untouched by the
  merge — neither overlaps the `cli_args`/`folder_path_test.py` rewrite. `requirements.txt`
  moved one pin (`comfyui-embedded-docs` 0.5.10→0.5.11); a scoped dry-run install of that pin
  alone shows only that package under "Would install", confirming it does not pull in torch or
  torchvision. Validation: this session has no GPU runtime and no installed dependencies at all
  (fresh scratch clone — not even numpy is present, let alone torch/comfy_kitchen), so the full
  reinstall and the GPU acceleration check are unrun; do both on the next session that holds a
  live installation. All 21 changed/added Python files (7 `comfy`/`comfy_extras` sources plus
  `folder_paths.py`, `nodes.py`, and 13 test files) byte-compiled clean with `py_compile`.
  Attempted imports of the seven changed `comfy_extras.*` modules all failed on missing
  dependencies (`torch`, `numpy`, `kornia`, `av`, `typing_extensions`, `comfy_kitchen` — none
  installed here), so the import-check half of validation could not run in this container;
  `py_compile` is what stands in for it, per the pattern the two entries below already
  established for a dependency-less session. Full-tree conflict-marker sweep is zero. No
  pre-merge baseline test run was possible (no pytest here either), so there is no Gate 6 diff
  for this sync. (This entry supersedes and folds in what would otherwise be a separate
  2026-09-06 entry for `ab02f366`/`15eb748b` — that merge landed on `origin/main` directly
  from the stray branch between this session's merge and its push, so the reconciliation
  merge here carries no additional content beyond what is already described above; see the
  "three commits already reviewed" sentence.)
- 2026-09-05 (second sync): Adopted one upstream commit, `18ebc2af`, a lone `comfy-kitchen`
  pin bump from 0.2.31 to 0.2.33 (#16133). No source changed, so validation was the dry run,
  the install and an import check rather than a full compile pass. The dry run listed only
  `comfy-kitchen-0.2.33` under "Would install" — torch and torchvision absent, as required —
  and the install replaced 0.2.31 in place with nothing else touched. `import comfy_kitchen`
  succeeds and reports 0.2.33. The GPU acceleration check passed on both installs. Clean
  merge, no conflicts; the fork's two local fixes (`folder_paths.py`, `extra_config_test.py`)
  were not in the window and are untouched, and the fork surface is still those two files
  plus this one. The placeholder-deletion baseline was restored to its expected count after
  the merge, with nothing else modified or untracked.
- 2026-09-05: Adopted two upstream commits, `8a43c6bd` and `f00bfd61`, both partner-node
  maintenance. `8a43c6bd` adds GPT-6 Astra to the ChatGPT node along with a `reasoning`
  request field and a per-model effort table (`SUPPORTED_REASONING_EFFORTS`), so each model
  now advertises only the efforts it accepts. `f00bfd61` deletes nodes for models the
  vendors retired: the DALL-E 2 and DALL-E 3 nodes, the LTX-2 Pro and Fast text/image-to-video
  nodes, the Seedream 3.0 node and the Seedance 1.0 Lite models, and the Kling Video Extend
  node. Six files, +63/-861 — a net removal, so any saved workflow still referencing one of
  those nodes will now fail to load; that is upstream's intent, not a merge fault. Clean
  merge, no conflicts; the fork's two local fixes (`folder_paths.py`, `extra_config_test.py`)
  were not in the window and are untouched, and the fork surface is still those two files
  plus this one. `requirements.txt` unchanged, so no reinstall. Validation: all six changed
  modules byte-compiled and the four changed node modules imported cleanly; their
  `NODE_CLASS_MAPPINGS` are empty by design, as with the previous partner-node sync, because
  registration goes through the `comfy_entrypoint` extension API. GPU acceleration check
  passed on both installs. The placeholder-deletion baseline was restored to its expected
  count after the merge, with nothing else modified or untracked.
- 2026-09-04: Adopted one upstream commit, `250b2e95`, the Comfy Cloud partner nodes
  (#15935): a new `comfy_api_nodes/nodes_comfy_cloud.py` and `apis/comfy_cloud.py`, small
  additions to `util/client.py` and `util/download_helpers.py`, and a new test module.
  Clean merge, both local fixes untouched, `requirements.txt` unchanged so no reinstall.
  Validation: five changed modules byte-compiled and the new node module imported; GPU
  acceleration check passed on both installs. The new module registers through the
  `comfy_entrypoint` extension API, so its `NODE_CLASS_MAPPINGS` is empty by design.
- 2026-09-04: Adopted one upstream commit, `6e3c0bda`, a lone `comfy-aimdo` pin bump
  from 0.5.1 to 0.5.2. No source changed, so validation was the dry run, the install and
  an import check rather than a full compile pass; the GPU acceleration check passed.
  Repaired `refs/remotes/origin/HEAD`, which still pointed at a deleted branch and made
  tooling report the fork as untracked; `git remote set-head origin -a` re-resolves it.
- 2026-09-04: Adopted ten upstream commits through `acb2a019`: Comfy Compiler
  (CORE-389), Meta Muse Image nodes, Tripo node expansion, MiniMax H3 Max Turbo,
  workflow-templates 0.11.55 and node category updates. Clean merge, no conflicts;
  both local fixes above survived untouched. `requirements.txt` moved two pins
  (workflow-templates 0.11.54 to 0.11.55, comfy-aimdo 0.4.15 to 0.5.1) and was
  reinstalled after a dry run confirmed torch, torchvision and onnxruntime were
  absent from the plan. Validation: 22 changed modules byte-compiled and imported,
  GPU acceleration check passed. Corrected the `paths.txt` command above, which
  captured its own output file on first real use.
- 2026-09-04: Documented the sync procedure, the symlink
  merge trap, and the dependency and ONNX Runtime constraints here, so a session
  holding only this fork can sync it correctly. Host-specific paths and
  inventories stay in the untracked host notes.
- 2026-09-02: Adopted two upstream commits through `345c9190`: document-canvas
  metadata for ImageCompositor and the Windows single-GPU warning. Neither
  change required fork-specific code. Fixed three pre-existing Windows unit
  failures with the local fixes above. Installation handoff retained locally and
  untracked. Isolated validation: 1,526 unit tests passed (17 skipped), 274
  execution tests passed (7 skipped); Ruff, Pylint, and installation GPU checks
  passed.
