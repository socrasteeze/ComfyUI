# Local image prompt guides

Version 1.1.0 | Research checked 2026-09-09

Use one profile as the system prompt for your local Qwen chat in LM Studio. Send the image idea as the user message. The profile tells Qwen how to rewrite the idea for one image model.

These files do not install models, connect to ComfyUI, change sampler settings, or generate images. They define the prompt-writing stage:

```text
Your request -> local Qwen + one profile -> finished prompt -> your image workflow
```

## Files

| File | Use |
| --- | --- |
| `profiles/qwen-image-edit-2511.system.md` | Qwen-Image-Edit-2511 reference-based edits. |
| `profiles/flux2-klein-4b.system.md` | FLUX.2 [klein] 4B generation and editing. |
| `profiles/flux2-klein-9b.system.md` | FLUX.2 [klein] 9B generation and editing. |
| `profiles/anima.system.md` | CircleStone Labs Anima, with checkpoint-aware handling. |
| `profiles/illustriousxl.system.md` | IllustriousXL, with conservative derivative-aware defaults. |
| `RESEARCH_NOTES.md` | Evidence, scope, uncertainty, and source links. |
| `VALIDATION_CASES.md` | Manual tests for the prompt writer. |
| `output.schema.json` | Optional validation schema for the writer's JSON output. |

Every system profile contains its own complete operating rules. No shared file needs to be loaded beside it. Do not paste all five profiles into one system prompt.

## Set up in LM Studio

1. Open a new chat using your configured Qwen model.
2. Open that chat's system-prompt field.
3. Paste the entire matching `.system.md` file into the field.
4. Save the configuration as a named Preset, such as `Image prompts - Klein 9B`.
5. Start a separate chat for each target and apply its matching Preset.
6. Run the relevant tests in `VALIDATION_CASES.md`.

LM Studio documents Presets as reusable bundles of a system prompt and inference parameters. These Markdown files are system-prompt text, not native LM Studio preset JSON. Use the application's Preset controls to save them. A downloaded Markdown file does not activate itself. [L1]

Leave the model's chat/prompt template on its normal automatic configuration unless there is a separate template problem. The model template formats roles and messages. It is not the field for these image-writing instructions. [L2]

Separate chats and Presets provide the requested separation. You do not need five different sets of writing-model weights for these guides. The same Qwen model can use a different profile per conversation. API use should likewise supply the selected profile as the system message for each conversation.

Do not rely only on attaching the guide as a searchable document. This pack is designed to be loaded as the system instructions, not retrieved as occasional reference passages.

## Give each instance its actual checkpoint

The filenames above identify the intended image model, not the Qwen language model loaded in LM Studio.

Optional one-time configuration: add the exact image checkpoint and any relevant workflow behavior to the saved Preset when known. Ordinary requests do not need this metadata. You can add these lines below the profile's instructions:

```text
Checkpoint: exact image checkpoint filename here
Workflow: ComfyUI; state whether negative conditioning is active and which prompt parser is used
```

Only claim behavior that you have confirmed. A UI field's existence does not establish that the sampled model uses it.

The Klein profiles cover the user's "Klein2 Flux 4B" and "Flux 9B" as FLUX.2 [klein] 4B and 9B. Their core language rules are deliberately shared. Do not use them for FLUX.1 or a different FLUX.2 family member. See the exact model cards in the research notes.

For Anima, configure the variant once when known. For IllustriousXL, configure the full checkpoint name when known because derivative-specific instructions should take priority over generic defaults. When unspecified, use the conservative defaults in the profile without interrupting routine requests.

## Daily use

Select the target-model Preset, type normally, and copy the rewritten prompt. The local Qwen language model is the writer. The selected image model is the target. Nothing in this step generates or edits an image.

Example with the Qwen Edit Preset already selected:

Your input:

```text
change the mans' shirt to black and make it so he is sitting with 1 knee up while lookin the other way
```

Expected response format:

```text
Change the man's shirt to black while retaining its original design and material. Reposition him into a seated pose with one knee raised. Turn his head and gaze in the opposite direction from the source image. Preserve his identity, facial features, hairstyle, other clothing, the background, and the original visual style. Adjust clothing folds and shadows naturally to match the new pose.
```

The default response is only the prompt. There is no required command, model-name prefix, form, explanation, or negative section. The example is an authored expected response, not output verified on your local model.

Ordinary requests need no special formatting:

```text
An adult woman with short black hair and green eyes. Black leather jacket,
full body, flat anime colors, white background. Keep it simple.
```

The default is a faithful rewrite. It does not automatically decorate the request with a lens, cinematic lighting, extra props, or a different style.

For a single-image edit, a normal edit request is sufficient. When using multiple references, supply roles:

```text
References: image 1 = identity and scene; image 2 = replacement jacket.
Replace the jacket on the person in image 1 with the jacket from image 2.
Keep the same face, pose, and background.
```

For controlled expansion:

```text
/expand
An illustrated repair robot in a workshop. Add useful visual detail,
but keep it as a flat-color illustration with one robot.
```

For a correction report:

```text
/explain
[Paste the prompt to correct here.]
```

Positive-only output is already the default. This optional control enforces it when additional fields might otherwise be returned:

```text
/positive
[Your request here.]
```

For separate positive and negative fields when the selected workflow supports them:

```text
/full
[Your request here.]
```

You can also say "include a negative prompt" in ordinary language.

For automation:

```text
/json
[Your request here.]
```

These controls belong to this pack. They are not native commands for the image models or guaranteed built-in LM Studio commands.

## Output handling

All five profiles return only the finished positive prompt for an ordinary request. The target profile still controls its structure: editing instructions, scene prose, tags, or mixed text. This is a workflow preference, not a claim that every model uses the same conditioning method.

Separate negative fields are returned only when explicitly requested or supplied, and only according to the target's workflow rules. `/full` requests the full supported layout. The writer never silently combines negative-field content with the positive text.

`NOTES:` appears only when necessary to retain supplied runtime settings or flag a material unresolved limitation. Routine rewrites do not need generic warnings or explanations. Do not paste notes into an image text encoder. `/positive` enforces strictly positive-text-only output.

The JSON form is:

```json
{
  "target_model": "FLUX.2-klein-9B",
  "positive_prompt": "An eye-level product photograph of a yellow ceramic cup against a gray background.",
  "negative_prompt": null,
  "parameters": {},
  "notes": []
}
```

Pass only `positive_prompt` into the positive prompt input. Route `negative_prompt` only to a confirmed active negative channel. Keep `parameters` separate from text conditioning. A nonempty parameter object is a record of supplied settings, not evidence that those settings were applied.

`null` means disabled or unconfirmed negative conditioning. An empty string means an available channel intentionally has no exclusion text. The adapter must implement the actual pipeline's requirements. In particular, the Qwen Diffusers example uses a blank negative string in an active classifier-free-guidance setup. Do not blindly turn every `null` into a blank string or alter guidance based on this wrapper. [Q1, Q3]

This wrapper is not a FLUX structured scene prompt. Sending all of its routing metadata to an image encoder would be a separate implementation choice, not the intended integration.

## Local images and privacy

When Qwen cannot inspect an image, describe the reference or declare its downstream role. A text-only writer can still formulate "use the jacket from image 2". It cannot verify what the jacket looks like. The image workflow must receive the actual image files.

Nothing in this pack requires a cloud request or an external tool. LM Studio documents local chat and local-server operation without internet after the required models and runtimes are available. External tools, plugins, update checks, downloads, and a separately configured image workflow must be assessed separately. The files do not change their networking behavior. [L3]

## Sampling and testing

Keep your working Qwen settings for the first test. This pack does not impose one temperature, thinking switch, or context length across unspecified Qwen versions. The full profile, user request, and response must fit the active context.

Compare raw and rewritten prompts in the image workflow. Hold the checkpoint, references, seed, dimensions, sampler, guidance, and other settings fixed within each comparison. Repeat across several seeds before calling an improvement reliable. Do not use a single attractive image as evidence that all rewrites improved.

Review missed constraints before adding more adjectives. Test subject count, identity, text, framing, reference assignment, and style preservation separately.

## Limits

The guides standardize the rewrite and reduce avoidable mistakes. They cannot guarantee image-model adherence, accurate unseen details, exact spelling in rendered text, or pixel-perfect preservation. They do not make a missing ControlNet, reference adapter, mask, embedding, or LoRA appear.

The pack was researched and statically checked here. It has not been executed against your local Qwen instance or your image checkpoints. `VALIDATION_CASES.md` contains tests to run, not claimed passing model results.

## Sources for setup

- [L1] [LM Studio Presets](https://lmstudio.ai/docs/app/presets)
- [L2] [LM Studio prompt templates](https://lmstudio.ai/docs/app/advanced/prompt-template)
- [L3] [LM Studio offline operation](https://lmstudio.ai/docs/app/offline)
- [Q1] [Qwen-Image-Edit-2511 model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- [Q3] [Diffusers Qwen image pipelines](https://huggingface.co/docs/diffusers/api/pipelines/qwenimage)
