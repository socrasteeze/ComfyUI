# Research notes and source map

Checked: 2026-09-11 | Pack version: 1.2.0

## Revision 1.2.0

Added one profile: Krea 2, a Krea AI text-to-image model. This revision was researched against the model's own Hugging Face cards, the official Diffusers pipeline docs, the identity-edit LoRA's project page, and the fork owner's own SwarmUI notes (`Model Support.md`, `T2IModelClassSorter.cs`) for fork-specific facts (checkpoint count, the `krea2_raw_bf16` variant name, text-encoder/VAE wiring). No local-model execution informed the researched content; the dry-run harness checks the writer's mechanical behavior separately.

## Revision 1.1.0

This revision changes the interaction contract, not the researched model behavior. Every profile now defaults to a plain-language request in and a positive prompt out. Separate negatives are opt-in. A selected profile already establishes the model target. A generic reference edit does not require the prompt writer to see the source image. The exact shirt, seated-pose, and gaze example was added. No new external source review or local-model execution was performed for this revision.

## Evidence standard

Sources below are model-developer model cards, developer documentation, or the official implementation library documentation. No community prompt recipe is presented as a universal model requirement.

Three things must remain distinct:

- **Documented behavior:** what the linked model card or implementation says.
- **Compiler policy:** original rules in this pack for preserving intent, formatting responses, resolving contradictions, and handling missing information.
- **Workflow dependency:** behavior that needs the actual checkpoint, parser, node graph, or sampler configuration.

Architecture alone is insufficient to select every prompt convention. Variant-specific training and the text parser also matter. The pack therefore fixes a target family but accepts a declared checkpoint and workflow.

## Qwen-Image-Edit-2511

The exact model card supplies natural-language editing examples, separate image inputs, and a multi-image pipeline. It identifies improved consistency and viewpoint-editing capability. The older edit-family article supplies background on local appearance edits, semantic changes, and text replacement. Neither source makes this pack an official Qwen system prompt. [Q1, Q2]

Use the exact 2511 card as the anchor. Do not import the text-to-image suffixes or prompt-expansion templates from Qwen-Image-2512 merely because they share a repository. The profile's change/result/preserve structure is a practical writing policy, not a required command grammar.

Negative prompting is conditional on the implementation. The Diffusers documentation distinguishes true classifier-free guidance from other guidance parameters. A supplied negative can be ineffective when the corresponding guidance branch is inactive. The pack leaves runtime changes to the user. [Q3]

## FLUX.2 [klein] 4B and 9B

The two exact model cards establish the target scope: compact Klein models with generation and editing support. The standard releases are distilled; this pack does not force their sampling values onto a Base checkpoint. [F1, F2]

BFL's current documentation uses shared image-prompting pages. This pack uses that guidance without claiming that every hosted feature or limit transfers to local Klein. It does not assert different tag languages for 4B and 9B.

The shared building guide favors clear subjects and relevant detail. The technical page explicitly distinguishes Klein from hosted variants that expand prompts. The single- and multi-reference pages emphasize edit scope and reference roles. Typography and structured scene JSON have separate guidance. [F3-F8]

The positive-only default is conservative. It is not a claim that custom local guidance implementations can never accept a negative prompt. Any exception must identify a working negative-conditioning path.

## Anima

Use the CircleStone Labs model card linked below as the authority for the variant-specific conventions summarized inside the profile. This pack chooses conservative defaults when the checkpoint is unknown. Its hybrid output layout is a house policy, not a requirement to duplicate every concept in both tags and prose. [A1]

Do not assume that sharing a Qwen-family text component makes this image model a chat model. The writer must still target the image model's documented caption conventions and actual workflow.

## IllustriousXL

The early official card documents an SDXL-based illustration model, Danbooru data, composition-tag cautions, and positive/negative examples. Its series update also discusses natural-language capability. The later model cards establish additional release variants, including a stabilized v2.0 checkpoint. [I1-I3]

Tag-first is therefore a practical default for local Illustrious workflows, not a claim that the model cannot understand sentences. The pack does not copy an early negative example wholesale into every derivative. Nor does it treat Pony score tags or external embeddings as baseline requirements.

The suggested tag order and minimal artifact negatives are compiler policies. For a named derivative, use that developer's instructions when they conflict with a generic policy.

## Krea 2

Krea 2 is a 12B flow-matching text-to-image diffusion transformer from Krea AI, released as an undistilled `Raw` checkpoint and an 8-step-distilled `Turbo` checkpoint, with an official Raw-to-Turbo LoRA. [K1, K2, K5] Both cards are the developer's own model cards; the Diffusers pipeline page documents the architecture (single-stream MMDiT, Qwen3-VL text conditioning fused into the transformer). [K3]

**Documented behavior:** the checkpoint split (Raw vs. Turbo) and their respective step/CFG defaults, the Qwen3-VL text encoder and Qwen-Image VAE family, the absence of a tag-based prompting convention (both cards demonstrate descriptive prose and warn that "prompt style, specificity, language, and phrasing" affect adherence), and the model's internal NSFW text-refiner. [K1, K2, K3]

**Compiler policy:** the natural-language-only default (no tag/prose hybrid, unlike Anima or IllustriousXL), the CFG-1-implies-positive-only default carried over from this pack's Klein/Anima-Turbo precedent, and the decision to treat the identity-edit LoRA's fixed image order as a declared-workflow exception rather than default behavior are original policies for this pack, not claims from the model cards.

**Workflow dependency:** whether reference images reach the core transformer (they do not, by default — only the text encoder sees them) is documented on the model card itself, but whether an *edit* actually happens depends entirely on the fork's own unofficial identity-edit LoRA and its dedicated ComfyUI node pack. [K1, K4] That LoRA's fixed two-image order (scene = image 1, person = image 2) and its CFG guidance for edits vs. removals are documented on the LoRA's own project page, not on Krea 2's model card. [K4] The fork's checkpoint count (11) and the `krea2_raw_bf16` variant name are fork-internal facts from the maintainer's own SwarmUI notes, not from Krea AI. [S1]

Confidence: the base-model facts above are solidly sourced to the developer's own cards. The identity-edit workflow facts are sourced to a third-party (non-Krea-AI) LoRA project page describing an unofficial extension — treat that layer as workflow-dependent, not as Krea 2's own documented behavior, exactly as the profile's Target rules section says.

## Decisions that are not official benchmark findings

The pack's faithful-rewrite default, output controls, target lock, JSON wrapper, exact-string protection, parameter separation, and test cases are original workflow design.

There is no verified universal ideal prompt length for the user's unspecified pipelines. There is no claim that the 4B guide must be shorter than the 9B guide, or that adding quality words always helps.

No local generation comparison was run. The examples demonstrate formatting and intent preservation, not measured image quality. Do not describe the validation cases as passed until they are run against the user's models.

## Refresh procedure

When a checkpoint or workflow changes, inspect its developer's model card and its actual inference path. Update only the affected profile. Record the date and the exact variant. Re-run the relevant validation cases. Avoid applying an online platform's hidden prompt rewriting, node setup, or presets to raw local weights by assumption.

## Primary sources

### Qwen

- **Q1:** [Qwen-Image-Edit-2511 model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- **Q2:** [Qwen-Image-Edit family article](https://qwenlm.github.io/blog/qwen-image-edit/). Published 2025-08-19. Family background, not a dedicated 2511 prompt manual.
- **Q3:** [Diffusers Qwen image pipelines](https://huggingface.co/docs/diffusers/api/pipelines/qwenimage). Used for negative-conditioning semantics, not universal ComfyUI parameter names.
- **Q4:** [Official Qwen-Image repository](https://github.com/QwenLM/Qwen-Image). The repository distinguishes 2511 editing from other image-generation releases.

### FLUX

- **F1:** [Klein 4B model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)
- **F2:** [Klein 9B model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B)
- **F3:** [Building a good prompt](https://docs.bfl.ai/guides/prompting_unified_building)
- **F4:** [Technical parameters and positive phrasing](https://docs.bfl.ai/guides/prompting_unified_technical)
- **F5:** [Single-reference editing](https://docs.bfl.ai/guides/prompting_editing_single_reference)
- **F6:** [Multi-reference editing](https://docs.bfl.ai/guides/prompting_editing_multi_reference)
- **F7:** [Style and text](https://docs.bfl.ai/guides/prompting_unified_style)
- **F8:** [Structured scene JSON](https://docs.bfl.ai/guides/usecases_t2i_json_prompting)

### Anima

- **A1:** [CircleStone Labs Anima model card](https://huggingface.co/circlestone-labs/Anima)

### IllustriousXL

- **I1:** [Early-release model card and series update](https://huggingface.co/OnomaAIResearch/Illustrious-xl-early-release-v0)
- **I2:** [Illustrious XL v1.0 model card](https://huggingface.co/OnomaAIResearch/Illustrious-XL-v1.0)
- **I3:** [Illustrious XL v2.0-STABLE model card](https://huggingface.co/OnomaAIResearch/Illustrious-XL-v2.0)

### Krea 2

- **K1:** [Krea 2 Turbo model card](https://huggingface.co/krea/Krea-2-Turbo)
- **K2:** [Krea 2 Raw model card](https://huggingface.co/krea/Krea-2-Raw)
- **K3:** [Diffusers Krea 2 pipeline docs](https://huggingface.co/docs/diffusers/api/pipelines/krea2)
- **K4:** [Krea 2 identity-edit LoRA project page](https://huggingface.co/conradlocke/krea2-identity-edit). Unofficial, third-party; not a Krea AI source.
- **K5:** [Krea 2 open-source announcement](https://www.krea.ai/krea-2-open-source)
- **S1:** The SwarmUI fork's own `docs/Model Support.md` and `src/Text2Image/T2IModelClassSorter.cs`. Fork-internal maintainer notes, not a public URL; used only for fork-specific facts (checkpoint count, `krea2_raw_bf16` naming, text-encoder/VAE wiring), not for claims about Krea AI's own documentation.

### LM Studio

- **L1:** [Presets](https://lmstudio.ai/docs/app/presets)
- **L2:** [Prompt templates](https://lmstudio.ai/docs/app/advanced/prompt-template)
- **L3:** [Offline operation](https://lmstudio.ai/docs/app/offline)
