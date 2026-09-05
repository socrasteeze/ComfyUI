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
