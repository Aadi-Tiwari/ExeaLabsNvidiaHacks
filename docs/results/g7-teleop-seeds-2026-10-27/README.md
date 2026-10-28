# G7 / issue #62: 104 physics-checked counter_to_sink episodes from 14 human teleop seeds, 2026-10-27

Issue #62's bar: "a repeatable run produces at least 100 physics-checked `counter_to_sink` episodes from seeds, validates the dataset, and reports attempts, drops, throughput, and variation". The seeds are the P3 keyboard-teleop demos ([p3-teleop-2026-10-21](../p3-teleop-2026-10-21/), one human operator, hero_kitchen). The generator is Arrival's own object-centric SE(3) retargeting (`object_centric_se3_retarget`). This is **not upstream MimicGen**, which is still not integrated.

```bash
# extract p3-teleop-2026-10-21.zip (checksum in ../p3-teleop-2026-10-21/archive.sha256) to p3-teleop-2026-10-21/
python -m arrival retarget --room hero_kitchen --teleop p3-teleop-2026-10-21 --attempts 140 --seed 0 --res 64 --out out/g7
python -m arrival validate out/g7/datasets/hero_kitchen_se3_retarget --episodes --frames
python -m arrival cost --out out/g7 --json
```

## Results

| Measurement | Result |
|---|---|
| Human demos in the P3 run | 20 |
| Became seeds (replayed in today's sim, oracle passed again) | 14 ([seeds.json](seeds.json)) |
| Not used | 5 no longer pass on replay, 1 length outlier (13406 steps against a median near 450) |
| Retarget attempts | 140 (10 per seed) |
| Physics-checked episodes exported | **104** (74%) |
| Dropped | 36, all `physics_fail` (object not resting in the basin); 0 unreachable |
| Human contacts | 0 (no walking people in P3's tasks) |
| Validator | `validate --episodes --frames`: 104 episodes, 61894 frames, 0 flagged ([validate.txt](validate.txt)) |
| Wall time of the attempt loop | 1581.9 s on one CPU core, 236.7 demos/hour, 15.2 s per demo |
| Variation | 2 objects (bowl, mug), 5 instruction wordings, start offsets spanning 11.8 cm in x, 4.9 cm in y and 0.30 rad in yaw |
| Repeatability | A second run with `--attempts 200 --seed 0` gave identical outcomes for its first 111 attempts before it was stopped |

Per seed (10 attempts each, in [report.json](report.json) `per_source`): 11 of the 14 seeds give 6 to 10 successes. Two bowl seeds (P3 episodes 1 and 16) give 0 and one mug seed (episode 4) gives 1.

## Against the scripted expert and teleop

| | successes | seconds per success | what the seconds are |
|---|---|---|---|
| Teleop (P3) | 20 of 26 | 61.5 | operator time |
| Retargeted from teleop seeds (this run) | 104 of 140 | 15.2 | unattended wall time, one CPU core |
| Scripted expert (`sim --families counter_to_sink --episodes 40 --people 0 --res 64`) | 40 of 40 | 3.6 | unattended wall time, one CPU core ([expert_report.json](expert_report.json)) |

`arrival cost` reads this run next to the P3 baseline and reports `seconds_ratio_teleop_over_generated` 4.04 ([cost.json](cost.json)). Dollars are not measured: no cloud usage was metered, so `usd_per_success` is null.

## What the seeds turned out to be

The human demos mostly slide the object rather than lift it. Of the 14 seeds, 12 never raise the object more than 0.9 cm while the gripper is closed, one lifts it 8.6 cm, and one never closes the gripper at all. The scripted expert's handover rule (object lifted 15 cm) found no handover in any of them. So teleop seeds hand over from the object frame to the sink frame once the object has moved 2 cm (`teleop_seeds.MOVED`).

Replays use the recorded joint targets. The arm follows them exactly: in episode 1 the joint states match the recording to 0.0 rad for the first 364 steps, until the hand opens on the object. Contact with the object, though, differs from the operator's machine. That is why 5 of the 20 demos no longer reach the sink and are not used.

## Limits

- One room and one operator, with no walking people.
- 64 px cameras.
- These are simulated episodes; no policy was trained on them here.
- The dataset (30 MB) is not committed. Rerun the command above to rebuild it.

Versions: [versions.txt](versions.txt).
