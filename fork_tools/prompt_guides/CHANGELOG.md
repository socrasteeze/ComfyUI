# Changes

## 1.2.0

- Added `profiles/krea-2.system.md` (target ID `Krea-2`), covering Krea AI's Krea 2 text-to-image model: the Raw/Turbo checkpoint split, its natural-language prompting register, the CFG-1 positive-only default, and the fork's unofficial identity-edit LoRA path as a declared-workflow exception rather than default behavior.
- Added `Krea-2` to `output.schema.json`'s `target_model` enum.
- Regenerated all non-interactive copies via `harness/patch_profiles.py`; the five existing non-interactive files are byte-for-byte unchanged.
- Registered `krea2` in `harness/dryrun.py`'s `PROFILES` dict and the applicable validation cases.
- Added two validation cases for Krea 2 to `VALIDATION_CASES.md`.
- No existing profile's target rules were modified in this revision.

## 1.1.0

- Made prompt-only output the default across all five profiles.
- Made separate negative output opt-in through ordinary language, supplied negative text, or `/full`.
- Made the target selection a preset-level choice instead of a repeated per-request requirement.
- Added explicit text-only operation: rewrite the request; do not generate images or submit workflows.
- Added single-reference handling without demanding an image upload to the prompt writer.
- Added relative-gaze and pose-change preservation rules.
- Added the user's black-shirt, seated-pose, raised-knee example.
- Added three manual validation cases.

The model-specific research content is retained. The revision was checked structurally, not tested against a running local Qwen or an image workflow.
