# MiniMax H3 reference-to-video A/B log

Every row is one generation of the same shot: a two-performer studio clip where
both performers are replaced from character sheets, motion and soundtrack kept.
Held constant unless the row says otherwise — seed `779289819277270`, two
reference images, one reference video, `simple` scheduler, and a prompt whose
`retention_analysis` reuses the source track.

Configuration is read back from each output's embedded `prompt` tag
(`ffprobe -v error -show_entries format_tags=prompt -of json <file>`), not from
the graph. Widgets and notes drifted from reality three separate times in this
log; the file did not.

## Runs

`A` = audio verdict, `V` = video verdict. Frames are the generated length, not
the reference's.

| # | Frames | Steps | Sampler | Shift | LoRA | Accelerators | A | V | Total |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 362 | 20 | res_multistep | 12/3 | – | Mem, Ref2VA Conservative | skip | clean | 32:49 |
| 2 | 362 | 20 | res_multistep | 12/3 | – | Mem, Sparse 0.15, FBC Fast | crash | – | – |
| 3 | 362 | 20 | res_multistep | 12/3 | – | Mem, Sparse 0.15, FBC Fast, Spectrum | fault | warping | 10:35 |
| 4 | 362 | 12 | res_multistep | 12/3 | – | Mem, Sparse 0.15, FBC Fast | – | warping | 15:14 |
| 5 | 362 | 12 | res_multistep | 12/3 | – | Mem, Ref2VA Balanced, Spectrum | fault | – | 26:01 |
| 6 | 362 | 8 | res_multistep | 12/3 | Turbo | Mem, Ref2VA Balanced (0 cached) | fault | good | 16:37 |
| 7 | 362 | 20 | res_multistep | 12/3 | – | Mem, Ref2VA Balanced | fault | clean | 29:39 |
| 8 | 362 | 20 | res_multistep | 12/3 | – | Mem, Sparse 0.5, Ref2VA Balanced | fault | – | 31:26 |
| 9 | 362 | 20 | res_multistep | 12/3 | – | Mem, FBC Fast, Spectrum | fault | smear, identity | ~13:00 |
| 11 | 362 | 20 | res_multistep | 12/3 | – | Mem, Ref2VA Balanced | fault, loops | – | – |
| 12 | 362 | 20 | res_multistep | 12/3 | – | Mem, Sparse 0.15, FBC Fast, Spectrum | fault | smear | 13:55 |
| 13 | 362 | 20 | res_multistep | 12/3 | – | Mem, FBC Fast, Spectrum | fault | good | – |
| 14 | 362 | 20 | res_multistep | 12/3 | – | Mem, FBC Fast, Spectrum | fault | good | – |
| 15 | 362 | 20 | res_multistep | 12/3 | – | **Mem only** | fault | – | – |
| 16 | 362 | 20 | res_multistep | 12/3 | – | Mem, FBC Fast, Spectrum | fault | – | – |
| 17 | 362 | 8 | euler | 8/5 | Turbo | Mem, Ref2VA Balanced | fault | good | – |
| D1 | 294 | 8 | euler | 8/5 | Turbo | Mem, Ref2VA Balanced | **clean**, last 1 s drifts | good | – |
| D2 | 294 | 25 | res_multistep | 12/5 | – | Mem, FBC Fast, Spectrum | fault | good | – |
| D3 | 243 | 25 | res_multistep | 12/5 | – | Mem, Sparse 0.5, Ref2VA Aggressive, Spectrum | fault | good | – |
| D4 | 124 | 8 | euler | 8/5 | Turbo | Mem, Sparse 0.5, Ref2VA Aggressive | **clean** | good | 2:29 |
| D5 | 243 | 8 | euler | 8/5 | Turbo | Mem, Sparse 0.5, Ref2VA Aggressive | fault | – | – |
| **B** | **294** | **8** | **euler** | **8/5** | **Turbo** | **Mem, Ref2VA Aggressive** | **clean** | **clean** | – |

Rows 1–17 are `MiniMax_H3_000NN`; D-rows are the DaSiWa workflow's own
`MiniMax_H32026-09-13_0000N`. Row B is `MiniMax_H3_00015`, the baseline.

Two external clean runs for reference: a SwarmUI generation at 294 frames, 20
steps, no LoRA; and the DaSiWa D1 above.

## What the columns settle

**Generation length dominates everything.** No 362-frame run produced clean
audio, including row 15 with every accelerator removed. 362 is the top of the
node's stated trained range. 294 is the working ceiling; 124 and 294 both came
back clean.

**The soundtrack must match the generation.** A reference clip longer than the
generation leaves the audio unreconciled — the video is capped to the frame
count and snapped to the 17k+5 grid, the soundtrack is not. Rows 1–10 ran a
17.1 s clip against a 12.25 s generation.

**Accelerator ranking.** Ref2VA is the only cache safe at 294; its mode is
irrelevant under the Turbo LoRA because it caches nothing there (0 of 8 steps,
every time). FirstBlockCache and Spectrum broke audio at 294 even where video
was good. Sparse Attention at 0.5 cost 8.6 % per step against off at 1216×672
and broke audio at 243 — it does not pay at this canvas.

**What made no difference.** The `partially_copy` → `fully_copy` retention tag;
moving the soundtrack from the paired `ref_video_audio_N` socket to the
standalone `ref_audio_N`; resolution between 0.65 and 1.0 MP; split versus
paired wiring once the reference length matched.

## Baseline

Row B. 294 frames, 0.8 MP (1216×672), Turbo 8-step LoRA at strength 1.0,
`euler` / `simple` / 8 steps, sigma shift 8/5 video/audio, Memory Optimization,
Ref2VA, reference video trimmed so its soundtrack equals the generation length,
paired on `ref_video_audio_0`.

## Open

- The `ref2va` checkpoint has a known training-quality issue; fl2va-based
  hybrids exist. Untested here.
- Whether 277 frames clears the last-second drift seen on D1.
- Whether Sparse pays at a larger canvas than 1216×672.
- Resolution headroom: `ResolutionSelector` at 1.0 MP with `multiple` 32 yields
  1376×768, which is over the model's own pixel cap; `multiple` 64 yields
  1344×768, which is exactly it.
