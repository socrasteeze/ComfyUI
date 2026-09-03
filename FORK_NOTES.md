# Fork Maintenance

## Sync Contract

- Fetch upstream changes from `Comfy-Org/ComfyUI`, branch `master`.
- Publish only to this fork's `origin/main`. Never push to `upstream`.
- Preserve upstream model, node, workflow, and API compatibility.
- Keep installation inventories and machine-specific handoffs local and untracked.
- Local model, input, and output folders may be symlinks. Never restore tracked
  placeholders through them. Consult the excluded `CLAUDE.md` before local work.
- Verify the installation's GPU acceleration after merging or changing packages.

## Local Fixes

- Classify `.m2v` as video explicitly; it is absent from some system MIME tables.
- Use a native absolute temporary home path in the extra-config test fixture.
  A root-relative Unix path is not an absolute Windows home path.

## Verification

Use the repository's CI commands. Portable Python can hard-code the live checkout
in its `._pth` file; verify `folder_paths.__file__` before testing a worktree.
Test child processes must resolve the same isolated Python and checkout. A test
server connecting to an existing live server is not a valid execution baseline.

Keep custom nodes, models, user databases, and test output outside the verification
checkout's published changes. Record baseline failures by test name and cause.

## Sync Log

- 2026-09-02: Adopted two upstream commits through `345c9190`: document-canvas metadata for
  ImageCompositor and the Windows single-GPU warning. Neither change required
  fork-specific code. Fixed three pre-existing Windows unit failures with the
  local fixes above. Installation handoff retained locally and untracked.
  Isolated validation: 1,526 unit tests passed (17 skipped), 274 execution tests
  passed (7 skipped); Ruff, Pylint, and installation GPU checks passed.
