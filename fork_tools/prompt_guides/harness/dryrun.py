"""Dry-run every local-image-prompt-guides profile against VALIDATION_CASES.md.

One fresh conversation per (profile, case) - the pack requires chat isolation.
Multi-turn cases keep their own history. Output is written as JSON for grading.
"""
import json
import os
import sys
import time
import urllib.request

# Ollama base URL. Set PROMPT_GUIDES_OLLAMA to point at a remote server.
HOST = os.environ.get("PROMPT_GUIDES_OLLAMA", "http://127.0.0.1:11434").rstrip("/")
MODEL = sys.argv[1] if len(sys.argv) > 1 else (
    "hf.co/llmfan46/gemma-4-26B-A4B-it-ultra-uncensored-heretic-GGUF:Q4_K_M")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "profiles-noninteractive")
OUT_NAME = sys.argv[3] if len(sys.argv) > 3 else "dryrun.json"

PROFILES = {
    "klein9b": "flux2-klein-9b.system.md",
    "klein4b": "flux2-klein-4b.system.md",
    "qwenedit": "qwen-image-edit-2511.system.md",
    "anima": "anima.system.md",
    "illustrious": "illustriousxl.system.md",
    "krea2": "krea-2.system.md",
}
ALL = list(PROFILES)
EDITS = ["qwenedit", "klein9b", "klein4b"]

# (case id, applicable profiles, [turn, turn, ...])
CASES = [
    ("1 faithful style", ALL, [
        "One red repair robot holding a blue toolbox. Flat anime colors.\n"
        "Full body, plain white background. Keep the idea simple."]),
    ("2 scoped edit", EDITS, [
        "Recolor only the jacket olive green. Keep the same person and scene."]),
    ("3 reference roles", EDITS, [
        "References: image 1 = person and scene; image 2 = pose guide;\n"
        "image 3 = coat. Keep the identity and scene from image 1.\n"
        "Use only the pose from image 2 and the coat from image 3."]),
    ("4 exact text", ALL, [
        'Replace the sign text with "ECHO-6 / BAY 04". Keep that exact punctuation.']),
    ("5a multi-view sheet", ALL, [
        "One character reference sheet. Exactly two rows and ten views.\n"
        "The front bust through the midriff is the largest identity view.\n"
        "White background. No boxes, dividers, labels, text, or palette.\n"
        "Keep the source character and art style."]),
    ("5b separate outputs", ALL, [
        # The pack runs 5b as a follow-up to 5a in the same chat; keep that.
        "One character reference sheet. Exactly two rows and ten views.\n"
        "The front bust through the midriff is the largest identity view.\n"
        "White background. No boxes, dividers, labels, text, or palette.\n"
        "Keep the source character and art style.",
        "Give me three separate prompts for the same source character:\n"
        "front full body, left-side full body, and rear full body.\n"
        "White background for each. One output image per prompt."]),
    ("6 conflicting framing", ALL, [
        "A single close-up face portrait and the entire body with shoes fully\n"
        "visible, both as the same one-view composition. Both are mandatory."]),
    ("7a deliberate artifacts", ["anima", "illustrious"], [
        "A rough monochrome pencil drawing of a stone tower. Visible paper\n"
        "texture and a deliberately worn scan. No people."]),
    ("7b artifacts + negative", ["anima", "illustrious"], [
        "A rough monochrome pencil drawing of a stone tower. Visible paper\n"
        "texture and a deliberately worn scan. No people.\n"
        "Include a separate negative prompt."]),
    ("8a anima aesthetic", ["anima"], [
        "Checkpoint: Aesthetic\nAn illustrated blue teapot on a wooden table."]),
    ("8b anima turbo+neg", ["anima"], [
        "Checkpoint: Turbo\nAn illustrated blue teapot on a wooden table.\n"
        "Negative: blurry, watermark."]),
    ("9 runtime/lora", ALL, [
        "/json\nWorkflow: I have not confirmed the prompt parser.\n"
        "Protected: myStyleToken\n"
        "<lora:my-style:0.7>, myStyleToken, a red robot on white.\n"
        "Seed 123. Width 1024. Height 1024. Steps 20."]),
    ("10 missing visual", ALL, [
        "References: image 1 will be supplied to the image generator later.\n"
        "Keep its subject identity and replace only its background with white."]),
    ("11 subject binding", ALL, [
        "Two adult women shake hands. The red-haired woman in the blue jacket\n"
        "is on the viewer's left. The black-haired woman in the yellow jacket\n"
        "is on the right. White background."]),
    ("13 everyday edit", ["qwenedit"], [
        "change the mans' shirt to black and make it so he is sitting with 1 "
        "knee up while lookin the other way"]),
    ("14a clean default", ALL, [
        "One red robot holding a blue box. Flat anime art. Plain white background."]),
    ("14b default + negative", ALL, [
        "One red robot holding a blue box. Flat anime art. Plain white background.\n"
        "Include a separate negative prompt."]),
    ("15 follow-up chain", ALL, [
        "A red robot holding a blue box.",
        "make the box green instead",
        "New prompt: a yellow ceramic cup on a gray background."]),
]


def chat(system, history, timeout=900):
    payload = {
        "model": MODEL, "stream": False,
        "messages": [{"role": "system", "content": system}] + history,
        "options": {"temperature": 0.7, "seed": 7, "num_predict": 2048},
        "think": False,
    }
    req = urllib.request.Request(f"{HOST}/api/chat",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["message"].get("content", "")


results = []
start = time.time()
for case_id, profiles, turns in CASES:
    for pname in profiles:
        system = open(os.path.join(GUIDES, PROFILES[pname]), encoding="utf-8").read()
        history, replies = [], []
        try:
            for turn in turns:
                history.append({"role": "user", "content": turn})
                out = chat(system, history)
                history.append({"role": "assistant", "content": out})
                replies.append(out)
        except Exception as exc:  # noqa: BLE001
            replies.append(f"<<ERROR {type(exc).__name__}: {exc}>>")
        results.append({"case": case_id, "profile": pname, "replies": replies})
        print(f"{case_id:<24} {pname:<12} ok ({int(time.time()-start)}s)", flush=True)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({"model": MODEL, "results": results}, fh, indent=1)
print(f"\n{len(results)} runs -> {out_path}  ({int(time.time()-start)}s total)")
