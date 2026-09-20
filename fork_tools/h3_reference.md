# MiniMax H3 — production reference

The consolidated answer to "what settings do I use, and what is already known?"
for H3 reference-to-video character swaps with the source soundtrack kept.

Consolidates the run logs, the accelerator findings, and the production rules
that were spread across several files and session notes. **Nothing here is new** —
every claim traces to a run in `h3_ab_log.md` or to a dated session.

Companion files:

| File | Role |
|---|---|
| `fork_tools/h3_ab_log.md` | Raw run table, 23 rows. The evidence. |
| `CHECKPOINT_RUNS.md` (host-only) | The one untested axis: which checkpoint holds identity. |

---

## 1. The config

The baseline is **row B** of `h3_ab_log.md` — the only run in 23 that came back
clean on both audio and video. Two items have since been superseded; both are
marked.

| | Value | Source |
|---|---|---|
| Frames | 294 (12.25 s) — *but see §2* | row B |
| Resolution | 0.8 MP = 1216x672 | row B |
| Sampler / scheduler | `euler` / `simple` | row B |
| Steps | 8 | row B |
| Sigma shift (video/audio) | 8/5 | row B |
| Distillation | ~~Turbo 8-step LoRA, str 1.0~~ -> **HyperFlow** | superseded 2026-09-19 |
| Accelerators | Memory Optimization + Ref2VA. **Nothing else.** | rows 3, 9, 12, D3, D5 |
| Reference video | trimmed so its soundtrack equals the generation length | rows 1-10 |
| Audio wiring | paired on `ref_video_audio_0` | row B |
| Guide pill | off — fails "controlnet file is invalid" on current core | — |

Chain order: Loader -> LoRA -> Mem -> (Sparse) -> Sigma Shift -> Ref2VA -> Guider.

**Never stack two distillations.** HyperFlow with the Turbo LoRA, or either on a
base that already merged turbo, is one distillation too many.

### Why HyperFlow replaced Turbo

Operator verdict, same seed and references: picture clearly better and livelier.
Cost 19:12 vs Turbo's 18:42 (main pass 85.3 vs 82.9 s/it; face pass identical at
42.0).

Its audio is jumbled from second one, and that is structural rather than a
setting: the trained grid's last video step falls 0.4688 -> 0 in one jump, and on
a pruned base the two-time (t, r) conditioning that teaches that jump cannot
attach, so the audio stream takes an undistilled 0.18 leap every step. Verified
that the 12/3 shift composes correctly — shift is *not* the fault.

This does not reach production **because the generated audio is discarded anyway**
(§4). On a pipeline that keeps H3's own audio, HyperFlow is not usable in this
form.

**Caveat:** every H3 base on hand is pruned (curve-form: `adaln_t_table` present,
no `time_embedder`), so this measures HyperFlow's reduced form, not the released
model. Unpruned int8 bases exist at 31.7 GiB — too large for a 32 GB card, given
the pruned run already peaked at 30.0 GB.

---

## 2. Generation length

`h3_ab_log.md` concluded that 362 frames breaks audio unconditionally: no
362-frame run produced clean audio, including row 15 with every accelerator
removed, and 294 came back clean.

**That conclusion is workflow-specific, not a property of the length.** On
2026-09-19 a 362-frame ref2va piece rendered with clean audio end to end through
a different graph (Continuity), 8-step, euler/simple, shift 8/5, 600p reference.

So: 294 is the safe number on the logged workflow. 362 is reachable but must be
re-verified per graph. 362 is the top of the node's stated trained range either
way.

---

## 3. Accelerators — ranked, with the mechanism

**Mechanism first, because it explains the whole ranking.** H3's audio and video
run on *different sigma schedules*. Audio velocity is scaled by
d(sigma_a)/d(sigma_v), which runs 4.00 at sigma_v=1.0 down to 0.26 near 0 and
roughly halves between adjacent early steps. Any cache that decides which steps
to skip from the **video** stream and replays the cached residual onto audio
carries the wrong scale. Measured on EasyCache: audio at half amplitude with
missing bass while video SSIM held 0.95-0.96. (ComfyUI issue #15326; the fix in
#15390 gave EasyCache a separate audio accumulator, skipping only when both
streams agree.)

| Node | Verdict | Evidence |
|---|---|---|
| Memory Optimization | Safe, always on | every row |
| **Ref2VA** | **The only cache safe at 294** | row B, D1 |
| FirstBlockCache | Breaks audio at 294 even where video is good | rows 9, 12, D2 |
| Spectrum | Same family, same result | rows 3, 5, D2 |
| Sparse Attention 0.5 | Costs 8.6 %/step vs off at 1216x672, and broke audio at 243 | rows 7 vs 8, D5 |

Ref2VA survives because it has separate audio thresholds and hard-caps
consecutive cache hits at 1. FBC allows 2 — which is also the most likely
mechanism behind row 9's identity loss, since reference tokens ride every step
and two skipped in a row is where they stop asserting.

**Ref2VA's mode is irrelevant under an 8-step distillation** — it caches nothing
there, 0 of 8 steps, every time. Conservative/Balanced/Aggressive are the same
run.

---

## 4. Audio: generate it, then throw it away

For a swap that keeps the source track, **mux the source back in**. H3
re-synthesizes speech rather than copying it — a timing gap of ~0.1 s is enough
to drop words — and `fully_copy` in `retention_analysis` is a hint, not a
guarantee.

**Measure the offset every time.** H3's output ran a constant **155 ms ahead** of
the source in every 3 s window on one render; muxing with `-ss 0.155` on the
audio input brought it to zero. Do not assume 155 ms carries to the next render.

Measure with **spectral flux above 250 Hz, lag search limited to +/-300 ms**. An
earlier "+/-800 ms wander" finding was wrong — envelope cross-correlation on
bass-heavy music aliases to beat multiples.

### Still feed audio in

Feeding the source track in as a *timing driver* is what holds lip sync; it is
the generated output that gets discarded. A claim that reference audio through
the ReferenceToVideo path collapses identity (similarity 0.88 video-only vs
0.06-0.09 with audio) is **one user's post in HF discussion #91, disputed in
thread, no staff reply** — and row B was clean with paired audio. Treat it as
weak evidence.

Hard limits: reference audio 2-15 s per clip, 15 s total.

---

## 5. The reference clip

**Cut on a shot boundary.** A reference opening on even 14 frames (0.58 s) of the
previous shot makes H3 hold that framing for seconds — one clip cost several
13-25 minute renders before anyone looked at the reference's first second. In
that render faces landed ~50 px wide and came out artifacted.

Before using any clip as a reference, scene-detect it:

```bash
ffmpeg -i SRC -vf "select=gt(scene\,0.08),metadata=print:file=-" -f null -
```

Start the cut one frame after a boundary, and write one `[Shot N]` per detected
shot into the prompt.

**Match the soundtrack to the generation.** The node caps a reference video's
frames to the generation and snaps down to the 17k+5 grid, but hands the
soundtrack to `_encode_ref_audio` untruncated. A 17.1 s clip against a 12.25 s
generation leaves +4.859 s of unreconciled overhang — that was rows 1-10.

Trimming trap: `-t` alone lands 2 frames short and drops the reference to 277
frames, reopening a 0.72 s gap. **Overshoot with `-frames:v` and let the node cap
it.** And do not substitute a differently-rated source — a 29.97 fps file changes
the frame rate too.

---

## 6. Prompting: fix once, then reseed

**What the prompt controls:** lip sync quality, who vocalizes, which gestures the
subjects perform, whether invented motion appears. Fixing the prompt to the
Ref2VA guide moved audio match from swinging 0.30-0.85 by seed to a stable
0.84-0.87 on every run after.

**What it does not control:** cut placement and one-off gestures. Timestamps in
`At MM:SS.mmm` barely steer where cuts land — every render put them 0.4-1.5 s
early. A shush clause at the right timestamp did not produce one; removing the
clause did not prevent one. Two renders sharing a seed both showed an unprompted
shush at the source's timing; a third with the same prompt and a different seed
had none.

**Therefore: get the prompt guide-correct once, then treat the rest as a seed
lottery.** Every reword re-rolls the whole clip and historically wrecked the
audio match. To test a prompt edit without losing a good take, reuse the good
run's seed.

### Required prompt structure

Following MiniMax's own guide (`ComfyUI-Continuity/creator/families/h3/prompts/ref-en.txt`):

- Set the piece's `music` field to "`<Audio 1>` is directly reused 1:1 as the
  complete music and vocal track." **A blank box compiles to
  `non_diegetic_music: N/A`**, which contradicts the `<Audio 1>: fully_copy` line.
- Cite `<Audio 1>` inside the shot text.
- Write the vocalist as `(S@handle)` — expands to `<Subject N> (S1)`. Do not also
  write `@handle` before it.
- Use the source's real cut times in `At MM:SS.mmm`.
- No `<d>` lyrics needed; they may introduce new voices.
- **Do not invent choreography** for a subject meant to follow the source.
  Written-in gestures ("hands chopping the air") render literally and read as
  wrong. Write "moving exactly as the dancer does in @vid-1" instead.

Result on that structure: audio match 0.87, shush at the source's time
unprompted, operator verdict "essentially perfect".

---

## 7. Grading

**A/B every render against the source clip, not against the previous best.** The
target is the original video; the best run is itself still off. A comparison
against the current best can ride alongside, but it is secondary.

Each report leads with source-vs-render numbers and a source-over-render frame
strip at matching frame numbers: cut times vs the source's cuts, motion vs the
source's motion, generated audio vs the source track.

**Judge audio and video separately.** Several runs have good video and broken
audio; collapsing them into one verdict loses the signal.

**Sweep frames — do not trust averages.** Whole-clip motion averages hide tail
problems; a mid-clip freeze barely moves the number.

**Read config back from the output, never from the graph:**

```bash
ffprobe -v error -show_entries format_tags=prompt -of json OUTPUT.mp4
```

Widgets and notes drifted from reality three separate times in the A/B log. The
embedded prompt tag did not.

---

## 8. Diagnostics

### A run stalls at step 0

Signature of VRAM paging over PCIe: GPU 100 % util at ~115 W, memory-controller
util 1-5 %, `nvidia-smi dmon -s t` showing sustained ~60 GB/s rx and ~18 GB/s tx.
A healthy run draws 400-570 W with PCIe near zero.

**Read `nvidia-smi dmon -s put` first.** Low power at 100 % util is not proof of a
stall on its own; the PCIe counters are.

**The fix was a smaller reference video** — a 720p reference cached 114 MB of
reference latents and stalled; a 480p cut of the same clip cached ~55 MB and ran
clean at the same model and output resolution.

Unproven suspect for why the loader stopped making room: upstream `7a0b5eed`
(comfy-aimdo 0.5.5 + auto fast-disk) and `d39cdfdb` (text encoder always on GPU
under dynamic VRAM), both 2026-09-16, after the clean runs of 2026-09-13.
`--disable-dynamic-vram` is the proposed A/B and has never been run.

### A run crashes with FirstBlockCache

The comfy compiler frees FBC's GPU cache. Run with `--disable-comfy-compiler`.

---

## 9. Dead ends — do not re-litigate

Each of these consumed real time and is settled:

- **The `partially_copy` -> `fully_copy` retention tag.** Made no difference.
- **Split vs paired audio wiring** (`ref_audio_N` vs `ref_video_audio_N`). No
  difference once the reference length matched.
- **Resolution between 0.65 and 1.0 MP.** No difference to the audio fault.
- **Blaming accelerators for the audio fault at 362 frames.** Row 15 ran with
  every accelerator removed and still faulted. Every audio verdict in rows 1-14
  that convicted a node is void.
- **"Sparse 0.15 is too low" (row 4).** Wrong — row 9 smeared and lost identity
  with Sparse off entirely. FBC at 294 frames causes the warping.
- **Video-damage verdicts from rows 1-14.** All measured at 362 frames. Sparse
  0.5, Ref2VA Aggressive, FBC and Spectrum all produced clean *video* at 243-294.

Two resolution traps worth keeping: `ResolutionSelector` megapixels is a
**target**, not a scale factor — it computes `megapixels * 1024 * 1024`. At 1.0 MP
with `multiple` 32 it yields 1376x768, which is 2.4 % over H3's own `MAX_PIXELS`
of 1,032,192; `multiple` 64 yields 1344x768, exactly it.

---

## 10. Open

Ordered by value.

1. **The checkpoint axis — the one thing never tested.** All 23 rows of
   `h3_ab_log.md` hold the checkpoint fixed. `CHECKPOINT_RUNS.md` has the
   constants, the criterion (identity hold at the head turn) and a run order for
   the fl2va/ref2va hybrid family (b30-49 -> b25-49 -> b20-49 -> b15-49), and
   **zero rows filled**. The variant axis is monotonic, so it can be walked
   rather than sampled.
2. **Confirm HyperFlow on a second shot** before switching production over. One
   seed on one clip is the whole sample.
3. **Isolate the face pass.** It still samples on Turbo at denoise 0.45 — it
   cannot take HyperFlow's SIGMAS — so it may be eroding the gain. One run with
   the face pass off answers it.
4. Whether 277 frames clears the last-second drift seen on D1.
5. Whether Sparse pays at a canvas larger than 1216x672.
6. A smaller unpruned quant, if one ships — that would enable HyperFlow's real
   two-time recipe.

### Standing rule

**If a run changes more than one column from the run above it, the comparison is
dead.** That is how the 2026-09-16 head-turn identity fix was lost: it worked, and
which of three variables fixed it was never written down.
