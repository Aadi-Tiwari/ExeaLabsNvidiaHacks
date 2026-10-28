# Cosmos Transfer2.5 on Arrival's sim episodes (Oct 27, 2026)

NVIDIA Cosmos Transfer2.5-2B restyled three of Arrival's simulated episodes into photoreal kitchens. The model is guided by the episode's own edges, so the arm, the fixtures and the walkers stay where the physics put them, and only the materials and the light change. That is the point of the restyle stage (SIM-7a, to-do C5): a policy trained on these frames sees real-looking kitchens without the demos losing the physics check they passed.

`side_by_side.jpg` and `cosmos_side_by_side.mp4` show each input next to its output.

## What ran

| | |
|---|---|
| Model | `nvidia/Cosmos-Transfer2.5-2B`, `general/edge`, from the [cosmos-transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5) repo at `2ff49d0` |
| Control | Edge, computed by the model from each input (`preset_edge_threshold: medium`, weight 1.0) |
| Sampling | 35 steps, guidance 3, seed 1; the prompt is in each `spec_*.json` |
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Server Edition (96 GB) on a RunPod pod, about 55 GB in use |
| Time | About 8 minutes 15 seconds of generation per clip |
| Guardrail | NVIDIA's Cosmos guardrail was on; every output passed |

The inputs are the cinema camera of three episodes recorded with `arrival-film/footage/capture_sim.py`, each 93 frames at 1280×720 and 16 fps:

| Clip | Episode | Room |
|---|---|---|
| `fridge_93` | open_fridge | `kitchen_real_01`, a real kitchen scanned on an iPhone |
| `counter_to_sink_93` | counter_to_sink, two people walking | `hero_kitchen` |
| `open_drawer_93` | open_drawer, two people walking | `kitchen_real_01` |

## Geometry check

Every output frame went through `check_frame` from `arrival/render/variation.py`, the same check the restyle stage applies before it keeps a frame. It is the correlation of the input's and the output's edge maps, with 0.6 as the threshold (`EDGE_CORR_MIN`). Results are in `geometry_checks.json`.

| Clip | Frames kept | Edge correlation, median (min to max) |
|---|---|---|
| fridge_93 | 93 of 93 | 0.767 (0.737 to 0.789) |
| counter_to_sink_93 | 93 of 93 | 0.808 (0.773 to 0.825) |
| open_drawer_93 | 93 of 93 | 0.811 (0.767 to 0.824) |

## Limits

- This is three clips run by hand on a rented GPU, not the dataset run. The restyle stage still calls the model through its HTTP client (`COSMOS_URL`) on a tenth of each dataset's frames, and nothing here serves Transfer2.5 behind that endpoint yet.
- The edge check confirms that structure is kept, not that the result looks real. A person's look, a reflection or a texture can change inside the edges, and the walkers come out as pale mannequins.
- The fine-tuned GR00T in this repo was trained on the unrestyled frames. Whether restyled frames help the policy has not been measured.
