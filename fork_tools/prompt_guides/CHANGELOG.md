# Changes

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
