# HANDOFF

**Updated:** 2026-08-30 · **Branch:** master · **Base:** 8a33128f · **Tree:** dirty (untracked model placeholders only; no code changes)

Line cap bypassed by request — this handoff carries a full 16-item node-pack
evaluation and a sunset analysis that exist nowhere else.

## State

Evaluation session only; no code changed in this repo. 16 candidate node
packs/workflows were scoped against the installed stack and verdicts are final
below. Next session's work is installation of the four accepted items.

## Environment facts the verdicts rest on

- RTX 5090 32 GB, ComfyUI 0.34.0 portable, Windows.
- H3 checkpoints on disk: Dasiwa Hybrid4turbo/HybridTurbo, h3ErosMax_beta4,
  pruned INT8 ConvRot fl2va + ref2va (`models/diffusion_models/minimax/`).
- Flux2 Klein 4B/9B/9B-base on disk; ~8 Klein workflows in
  `user/default/workflows/`.
- Installed H3 acceleration: ComfyUI-MiniMaxH3-FirstBlockCache (cache axis),
  ComfyUI-SolAttn_triton (sparse axis, NVlabs Sol-Attn paper impl),
  ComfyUI-Spectrum-MiniMax-H3, ComfyUI-H3-Motion-Context-MultiRef.
- ControlNet folder is SDXL-era only — no Flux2 ControlNet models exist here.
- Ollama, QwenVL, JoyCaption present; kohya_ss dataset pipeline on E:.

## Verdicts — install (4)

1. **yanokusnir-ai/one-node-flux-2-klein** — 400★, 53 commits, last update
   2026-07-17, branch `master`. Consolidates T2I/I2I/EDIT/PAINT/FACESWAP/
   POSE/UPSCALE for Klein. Only hard dep (Inpaint-CropAndStitch) already
   installed; DWPose via controlnet_aux; SeedVR2 present. 9B is
   non-commercial license, 4B Apache-2.0.
2. **Civitai "Flux2 Klein Ultimate AIO Pro" workflow** (model 2390013,
   v4.1) — all six required node packs already installed. Superset of the
   local `Flux2 Klein SwapAnything V1.2 - Sam3` workflow; A/B and keep winner.
3. **BMB12d3/minimax-h3-prompt-composer** — 250★ standalone local HTML prompt
   builder for T2VA/I2VA/FL2VA/L2VA/Ref2VA. Touches nothing in ComfyUI.
4. **Zironic/H3-Optimizations — Memory Optimization node ONLY.** README
   confirms it runs standalone and its conflict handling disables its own
   sub-optimizations instead of clobbering foreign patches, so it is safe
   next to SolAttn. Do NOT enable its sparse attention (competes with
   SolAttn). No license file; ships prebuilt native binaries (unauditable).

## Verdicts — skip (12), with reasons for the record

- **BMB12d3/ComfyUI-H3-Ref2VA-Accelerator** (8★, 4 commits) — verified
  ~1.33x balanced on 5090; the installed FirstBlockCache's own committed
  benchmark on the same card + INT8 ConvRot is 1.44–1.49x. Its README forbids
  coexistence with FirstBlockCache AND Spectrum (both installed). Only
  differentiator is ref2va/audio-aware guards (quality, not speed). No license.
- **PlagueKind/ComfyUI-PlagueKind-Nodes** — H3 SLA (Triton, 5090-benchmarked
  1.4–1.75x) loses the incumbent slot to SolAttn; AdaLN LoRA fix restores
  ~0.02% signal (author calls it a logging cleanup). Rest is a utility grab-bag.
- **Zironic sparse attention** — same slot as SolAttn; SolAttn is
  paper-backed and already validated on this card with H3.
- **ckinpdx/ComfyUI-MMH3Tools** (22★) — best-in-class latent-domain chunk
  joining / music-video scheduling for long-form H3, but no long-form
  chunked work happens here today. Its keyframe carry path is untested by
  the author ("never generated a clip"); masked overlap is the only tested
  path. Revisit if long-form H3 starts. Needs 0.33+ PRs #15375/#15439/#15808
  (0.34.0 likely has them — unverified).
- **ckinpdx/ComfyUI-LlamaOmni** (7★, 1 commit, no docs) — redundant with
  QwenVL/JoyCaption/Ollama.
- **Hillobar/ComfyUI-Hillobar** (4★, 1 commit) — progressive-resolution H3
  sampler, a genuine third acceleration axis (claimed 1.6–2x) but excludes
  fl2va and replaces the sampler itself. Watch, don't run.
- **Hillobar/HARMON3** (3★, 8 commits) — desktop ref2va frontend; redundant
  with SwarmUI + direct ComfyUI, no auth on the Comfy API.
- **Damkohler/JLC-Flux2-ControlNet + jlc-comfyui-nodes** — zero Flux2
  ControlNet models on disk and no CN usage in any Klein workflow; utility
  pack duplicates kjnodes/rgthree/easy-use.
- **no8d/ComfyUI-NO8D-controls** (274★) — only unique fit is dataset-caption
  pairing for the kohya pipeline; revisit if that need materializes.
- **lumenastrum/clio-style-preview** (84★) — 397 style prompts for Krea2
  Turbo T2I; local Krea2 use is Ostris Edit, not style sweeps.
- **Pastebin NJrLkt5H** — Krea-2 Turbo T2I workflow JSON w/ style LoRAs not
  on disk. Link saved, nothing to implement.
- **BMB12d3/MiniMax-H3-Hybrid-Checkpoint-Builder** (6★) — byte-copy AdaLN
  overlay merger (FL2VA base + Ref2VA overlay); relevant to the Dasiwa
  hybrids already in use but only needed for custom merges. CPU-only tool.

## Rule discovered this session

H3 acceleration has three independent axes — sparse attention (SolAttn),
block/residual cache (FirstBlockCache), progressive resolution (none
installed). Exactly one per axis; same-seed A/B before trusting any change.
Current stack FirstBlockCache + SolAttn is the best-evidenced combo of
everything evaluated.

## Sunset analysis — recent in-house subject/character tooling vs Klein AIO

None of the three recent builds are sunset by the Klein AIO editor or
one-node-flux-2-klein; overlap is only "interactive single-image edit in the
Comfy GUI".

- **ComfyUI-subject-eraser** (custom_nodes, own repo): indexed deterministic
  subject selection (typed indices, spatial labels), Export Subjects JSON for
  HTTP callers — AIO has neither. Keep. Possible borrow: crop-and-stitch
  inpaint pass into its erase graph.
- **dataset-manager Subject Erase**: headless batch erase over loopback
  inside the curation pipeline (undo, promote flow). AIO can't fill that
  seat. Its next open items (linking-report port, headless Comfy job type)
  are unaffected.
- **SwarmUI Character Sheet extension**: multi-panel orchestration +
  ImageSharp compositing, model-agnostic engines (H3 ref2v, Qwen Edit Plus).
  Klein EDIT (multi-ref, up to 4 images) is a candidate THIRD engine for
  `SheetEngines.cs` — dodges Qwen's 3-ref text-encoder cap. AIO workflow is
  reference material for Klein multi-ref wiring, not a replacement. Both new
  SwarmUI extensions remain untested against a live backend — clear that
  checklist first (see that repo's HANDOFF).

## Install status (verified 2026-08-30 12:12, log `user/comfyui_8888.log`)

Both packs imported clean — one-node-flux-2-klein 0.0s, H3-Optimizations 0.6s,
no IMPORT FAILED, no conflict warnings. Registered node classes confirmed via
live `/object_info` on port 8888:
`FluxKleinOneNode`; `H3MemoryOptimization`, `H3SparseAttention`,
`H3SparseAttentionAdvanced`, `H3AIMDOResidencyLimiter`.
AIO Pro v4.1 workflow present as
`user/default/workflows/flux2KleinUltimateAIOProT2iI2iInpaint_v41.json`
(9 subgraphs, 64 distinct real node types) — **all 64 resolve, 0 missing**.

Correction to the earlier caveat: `native/` ships full CUDA source, CMake,
Dockerfile, PROVENANCE and an Apache-2.0 LICENSE — the `.dll`/`.so` are
buildable, not opaque. The pack root still has no license (Python side
all-rights-reserved).

Model refs in the AIO workflow were repointed on 2026-08-30 (4 widget values:
2 on subgraph instance node 6, 2 on loaders 759/92 inside subgraph c8077536):
`flux2-vae.safetensors` -> `Flux\flux2-vae.safetensors`, and
`qwen_3_8b_fp8mixed.safetensors` (absent) -> `qwen_3_8b.safetensors`.
Both verified present in the live VAELoader/CLIPLoader enums. Structure
diffed against the pre-edit copy: node/link/subgraph counts identical, exactly
4 widget diffs, no others. Empty 238-byte `Flux2-Klein-Ultimate-AIO.json`
deleted.

## Open

1. Open the AIO workflow in the UI and confirm the two loaders show the new
   values, then run one image. File was patched on disk, not through the UI.
2. A/B the AIO vs `Flux2 Klein SwapAnything V1.2 - Sam3.json`, same
   image/seed; keep the winner.
3. Same-seed H3 sanity run (ref2va, 5s) with and without
   `H3MemoryOptimization` — expected drift zero (chunking only). Any drift
   means something else is patching attention.
4. Grab the prompt-composer HTML for local use.
5. Decide whether the two Klein-capable packs are wanted in the SwarmUI
   ComfyUI backend too — see Traps; they are NOT there now.
6. Deferred: Klein engine for SwarmUI SheetEngines.cs — only after that
   repo's live-backend checklist clears.

## Traps

- Never enable two H3 sparse-attention or two cache nodes at once — silent
  quality drift, no error raised.
- Zironic and Ref2VA-Accelerator ship with NO license — all rights reserved;
  do not vendor their code into anything published.
- Zironic loads prebuilt native binaries from `native/` into the Python
  process — unauditable; weigh before install on any sensitive box.
- Evaluation was README-level + local-disk cross-reference; functional
  claims of the accepted items were NOT code-audited.
- The one-node repo uses branch `master`, not `main` — commit-history checks
  against `main` 404.
- **Two separate ComfyUI installs exist.** This one, and the SwarmUI backend
  under `dlbackend/comfy/ComfyUI` with its own 19-pack `custom_nodes` tree.
  The new packs, the whole H3 acceleration stack, subject-eraser, Impact
  Pack, easy-use, CropAndStitch and lora-manager are in THIS tree only, so
  the AIO workflow cannot run on the SwarmUI backend as-is.
- Patching a Windows path into a workflow through a shell heredoc corrupts
  `Flux\f...` into a formfeed (`\x0c`). It reads correct in terminal output.
  Build the separator as `chr(92)` in a script file and verify with `repr`.
- Subgraph workflows carry each model name TWICE — once on the loader inside
  `definitions.subgraphs`, once as a promoted widget on the instance node.
  Patch both or the UI and the executed graph disagree.
- The AIO file was rewritten with `indent=2`, so it is ~2.5x larger on disk
  than the Civitai original. Whitespace only; structure verified identical.
- Active log is `user/comfyui_8888.log`; `user/comfyui.log` is stale from
  January and will mislead any check that greps it.

## Verify

```powershell
# after installs: watch for import errors from the two new packs
Select-String -Path "user\comfyui.log" -Pattern "one-node|H3-Optimizations|IMPORT FAILED" -ErrorAction SilentlyContinue
```
