# Prompt-writer validation cases

These are original manual tests, not results from an executed local model. Use a fresh chat with one matching profile. Check behavior, not exact wording.

## 1. Faithful style preservation

Target: all profiles.

```text
One red repair robot holding a blue toolbox. Flat anime colors.
Full body, plain white background. Keep the idea simple.
```

Pass: one robot, red body, blue toolbox, full body, flat illustration, white background. No added camera brand, photorealism, workshop, second robot, or dramatic lighting.

## 2. Scoped edit

Target: Qwen Edit or either Klein.

```text
Recolor only the jacket olive green. Keep the same person and scene.
```

Pass: the jacket changes color; identity and unrelated elements are preserved. The prompt does not forbid changing all original colors or all pixels.

## 3. Reference role separation

Target: Qwen Edit or either Klein.

```text
References: image 1 = person and scene; image 2 = pose guide;
image 3 = coat. Keep the identity and scene from image 1.
Use only the pose from image 2 and the coat from image 3.
```

Pass: correct three-way mapping. No face or background transfer from the pose guide. No claim that the writer inspected an image it cannot see.

## 4. Exact text

Target: all profiles.

```text
Replace the sign text with "ECHO-6 / BAY 04". Keep that exact punctuation.
```

Pass: exact string is preserved. Edit-capable profiles describe replacement. A text-to-image profile does not pretend to have an edit image or mask; it preserves the requirement and flags the workflow dependency when needed.

## 5. Multi-view sheet versus separate outputs

Target: all profiles.

```text
One character reference sheet. Exactly two rows and ten views.
The front bust through the midriff is the largest identity view.
White background. No boxes, dividers, labels, text, or palette.
Keep the source character and art style.
```

Pass: one sheet, two rows, ten views, one largest identity view. No generic negative "multiple views". No claim of perfect unseen identity recovery. No invented view list unless expansion is requested.

Then test:

```text
Give me three separate prompts for the same source character:
front full body, left-side full body, and rear full body.
White background for each. One output image per prompt.
```

Pass: three complete prompts, not one triptych and not "same as above."

## 6. Conflicting framing

Target: all profiles.

```text
A single close-up face portrait and the entire body with shoes fully
visible, both as the same one-view composition. Both are mandatory.
```

Pass: one concise clarification. No silent choice, collage workaround, or claim that the two crops are identical.

## 7. Deliberate artifacts

Target: Anima and IllustriousXL.

```text
A rough monochrome pencil drawing of a stone tower. Visible paper
texture and a deliberately worn scan. No people.
```

Pass: preserves roughness, monochrome, paper, and aged-scan intent. The default output contains only the positive prompt. Repeat with a request for a separate negative prompt. The negative does not blindly forbid those characteristics.

## 8. Variant handling

Target: Anima.

```text
Checkpoint: Aesthetic
An illustrated blue teapot on a wooden table.
```

Pass: follows the profile's declared variant rule rather than assuming the unknown-checkpoint default. Check the model-specific quality rules in the profile.

Repeat with `Checkpoint: Turbo` and a supplied negative. Pass: output does not claim the unused negative is active; supplied unused constraints are retained in notes or positively expressed.

## 9. Runtime and LoRA separation

Target: all profiles.

```text
/json
Workflow: I have not confirmed the prompt parser.
Protected: myStyleToken
<lora:my-style:0.7>, myStyleToken, a red robot on white.
Seed 123. Width 1024. Height 1024. Steps 20.
```

Pass: valid JSON; exact trigger survives; seed, dimensions, and steps are recorded outside conditioning text. The unverified directive is retained and identified. The writer does not claim the LoRA was loaded.

## 10. Missing visual access

Target: all profiles.

```text
References: image 1 will be supplied to the image generator later.
Keep its subject identity and replace only its background with white.
```

Pass: a generic reference-based instruction or appropriate workflow caveat. No invented hair, outfit, age, or claim of seeing the image.

## 11. Subject binding

Target: all profiles.

```text
Two adult women shake hands. The red-haired woman in the blue jacket
is on the viewer's left. The black-haired woman in the yellow jacket
is on the right. White background.
```

Pass: two subjects with correct hair, jacket, and side assignments. No unbound attribute mixture presented as a guaranteed solution.

## 12. New chat isolation

Target: one Klein profile, then IllustriousXL in a fresh chat.

Use the same request from test 1. Pass: each response follows its active target's format. Prior-chat instructions do not cause the target to switch.

## 13. Everyday edit without commands or an attached image

Target: Qwen Edit. Select the profile before sending this message.

```text
change the mans' shirt to black and make it so he is sitting with 1 knee up while lookin the other way
```

Pass: returns only an edit prompt. Includes a black shirt, a seated pose, one raised knee, and gaze in the opposite direction from the source. Preserves identity and relevant unchanged content. Does not add a chair, choose a knee, choose left/right, demand the original pose, request a routine upload, explain prompting, or claim that an image was generated. No headings or stock negative prompt.

## 14. Uniform default output and optional negatives

Target: all six profiles, each in a fresh chat.

```text
One red robot holding a blue box. Flat anime art. Plain white background.
```

Pass: only one positive prompt, with no preamble, code fence, title, model name, explanation, negative field, or stock quality warning. The target profile determines the prompt's prose/tag structure.

Repeat with "Include a separate negative prompt." Pass: preserves the same visual requirements and follows the target's actual negative-channel policy. An explicit request does not make an unsupported or inactive negative branch work.

## 15. Follow-up changes versus independent requests

Target: all profiles.

First request a red robot holding a blue box. Then say "make the box green instead." Pass: returns the complete revised prompt with a green box and the original robot.

Then say "New prompt: a yellow ceramic cup on a gray background." Pass: does not inherit the robot, box, or previous style.

## 16. Krea 2 checkpoint and CFG handling

Target: Krea 2.

```text
Checkpoint: Turbo
A red ceramic teapot on a wooden table, soft window light.
```

Pass: descriptive natural-language prose (not a tag list), no invented camera brand or lens, positive-only output, `negative_prompt: null` in JSON mode.

Repeat with:

```text
Checkpoint: krea2_raw_bf16
Negative: blurry, watermark
A red ceramic teapot on a wooden table, soft window light.
```

Pass: treats `krea2_raw_bf16` as a Raw-family checkpoint. Does not silently discard the supplied negative; either applies it in a full/negative-requested layout or reports it in `NOTES:`/`notes` rather than dropping it.

## 17. Krea 2 identity-edit workflow dependency

Target: Krea 2.

```text
References: image 1 = a market street scene; image 2 = the woman.
Put the woman from image 2 into the street scene from image 1,
same outfit, walking toward the camera.
```

Pass: without a `Workflow:` line confirming the identity-edit LoRA and node pack, the writer does not assert that a reference-grounded edit is active; it writes the reference generically and flags the workflow dependency (in prose or `NOTES:`), rather than silently promising a Base/Turbo-checkpoint edit capability the model does not have by default.

Repeat with `Workflow: identity-edit LoRA and node pack loaded` prepended. Pass: preserves the fixed two-image order (scene = image 1, person = image 2) and does not reverse it.

## Image-quality comparison

After the writer passes the format checks, compare the raw request with its rewrite in the actual image workflow. Keep each pair's settings and references fixed. Repeat across multiple seeds. Record missed constraints and unwanted additions alongside visual quality.

These tests validate instruction handling. They do not prove generation accuracy or establish an optimal universal prompt.
