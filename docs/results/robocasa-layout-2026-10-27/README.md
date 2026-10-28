# G6 / TWN-4: twin layouts built in real RoboCasa (Oct 27, 2026)

Issue #69 asks whether the `layout.yaml` the compiler writes loads in RoboCasa, with core fixtures within 5 cm of
the twin. This run builds two twins with RoboCasa's own scene builder (`KitchenArena`, which runs
`scene_builder.create_fixtures`) and compiles each scene to a MuJoCo model with robosuite's `ManipulationTask`
(no robot): the authored `hero_kitchen` and the RoomPlan export `tests/fixtures/roomplan/kitchen_real_01.json`.

## Environment

GitHub Codespace, 4 cores, no GPU, Linux 6.8 (Azure). From `versions.txt`:

| | |
|---|---|
| arrival | `897aa05` (upstream main) plus this branch's new files |
| robocasa | github.com/robocasa/robocasa `2ce1aec`, version 1.0.1, `pip install --no-deps -e .` plus its requirements except `lerobot` and `tianshou` (they pull torch and are not used to build a scene) |
| robosuite | github.com/ARISE-Initiative/robosuite master `5ce6643` (1.5.2), `pip install -e .` |
| python / mujoco / numpy | 3.12.3 / 3.3.1 / 2.2.5 |
| RoboCasa assets | `python -m robocasa.scripts.download_kitchen_assets --type tex fixtures_lw` (textures 543 MB, fixtures 530 MB zipped; 1.9 GB unpacked). Objects were not downloaded; a layout needs none |

## Commands

```sh
# twins, with the repo's own CLI (the arrival environment, not the RoboCasa venv)
mkdir -p /tmp/scans/kitchen_real_01 && cp tests/fixtures/roomplan/kitchen_real_01.json /tmp/scans/kitchen_real_01/roomplan.json
python -m arrival demo --room hero_kitchen --episodes 1 --videos none --out out
python -m arrival demo --room kitchen_real_01 --from-roomplan --scans /tmp/scans --episodes 1 --videos none --out out

# RoboCasa build and comparison (RoboCasa's interpreter, run from the repo root)
MUJOCO_GL=osmesa <robocasa-venv>/bin/python scripts/check_robocasa_layout.py \
    out/twins/hero_kitchen out/twins/kitchen_real_01 --style 1 --json report_style1.json --save-layouts style1
# and the same with --style 5
```

Both exit 0. Full output: `out_style1.txt`, `out_style5.txt`; per-fixture numbers (centres, sizes, collision boxes,
origin offsets): `report_style1.json`; the layouts RoboCasa built: `hero_kitchen.robocasa.yaml`,
`kitchen_real_01.robocasa.yaml` (style 1).

## 1. `layout.yaml` as written: it loads, but RoboCasa builds a different room

RoboCasa reads the file without an error and MuJoCo compiles it (hero: 10 RoboCasa fixtures including walls and
floor, 30 bodies; kitchen_real_01: 11 fixtures, 57 bodies). What it builds (style 1):

| | hero_kitchen | kitchen_real_01 |
|---|---|---|
| walls | every wall 2.4 m off its line and 3.6 to 4.8 m too big | every wall 2.415 m off and 2.7 to 4.7 m too big |
| floor | 8.08 x 6.08 m for a 4 x 3 m room | 7.23 x 5.17 m for 3.58 x 2.54 m |
| fixture fronts | all 5 face the wall (180 degrees off) | all 6 face the wall |
| sink | not in its counter: no opening, centre 14.5 cm low inside a solid counter | (no sink) |
| stove | 14.6 cm into the floor | 15 cm into the floor |
| overlaps RoboCasa adds | sink in counter 2.7 cm | cabinet into the x = 3.58 m wall 7.1 cm, fridge into the y = 0 wall 17.9 cm |

Why: RoboCasa's `Wall` and `Floor` take half extents in their own rotated frame (`[half length, half height, half
thickness]`), a `wall_side` that turns the slab and pushes it outward by its thickness, and they ignore `z_rot`; a
row without `wall_side` is a `back` wall. A RoboCasa fixture faces -y at `z_rot` 0, the twin's faces +y at yaw 0. A
sink is an interior fixture the builder never moves: its counter has to place it (`interior_obj`). A fixture's `pos`
is its body origin, and the stove's origin is 0.146 m above the centre of its box.

## 2. `arrival.twin.robocasa_layout`: the same layout in RoboCasa's form

`robocasa_layout(layout.yaml)` reads only the layout (no RoboCasa import) and writes: walls with `wall_side` from the
side of the room they bound, half extents and the interior face as `pos` (`default_wall_th: 0` so the slab is exactly
the twin's); the floor in half extents; fixtures in one group per facing with `group_z_rot` = yaw + pi and the
position written in the group's frame; each sink as its counter's `interior_obj` with the `obj_x_percent` /
`obj_y_percent` that put it where the twin has it; and the body origin moved by RoboCasa's own `origin_offset`, which
the script reads on a first build and passes back. Oblique walls and types RoboCasa lacks stay explicit boxes. The
contract `layout.yaml` is unchanged (`scripts/check_layout.py` still checks it).

Placement below is the centre of RoboCasa's own exterior box of each fixture (`get_ext_sites`, its `main` region)
against the twin centre; walls by their collision box.

| style 1 | fixtures (RoboCasa incl. walls, floor) | worst fixture centre, horizontal | worst vertical | fronts | walls | overlaps RoboCasa adds |
|---|---|---|---|---|---|---|
| hero_kitchen | 5 of 5 (10) | 2.5 cm (counters) | 0 cm (sink excluded, below) | 5 of 5 match | 4 of 4 exact | none |
| kitchen_real_01 | 6 of 6 (11) | 0.0 cm | 0 cm | 6 of 6 match | 4 of 4 exact | none |

Style 5 (other fixture models and textures) gives the same table. Details:

- Counters: 2.5 cm and 5 cm short in depth because RoboCasa's `main` region leaves out the 5 cm front overhang; the
  counter top itself is centred on the twin.
- The hero sink sits in its counter's opening, 1.0 cm from the twin horizontally. Its height is RoboCasa's (top flush
  with the counter top), 5.5 cm below the hero twin's sink box, which stands 5.5 cm proud of the counter. The script
  reports it and does not count it against the 5 cm.
- Overlaps: the contacts deeper than 1 cm in the RoboCasa build are kitchen_real_01's wall/cabinet and wall/fridge
  pairs, 1.3 to 2.4 cm deep (style 1: 2.4 cm and 2.4 cm). The twin itself already has those (5 cm: RoomPlan puts the
  cabinet backs inside the wall's 10 cm thickness), so none is added. The hero twin's own overlaps (sink in counter
  19.5 cm by box, two 1 cm touches with walls) do not show as contacts.

## What this does not show

- `layout.yaml` itself is still the twin form; the RoboCasa form is produced by `robocasa_layout` (in tests offline,
  in the script with RoboCasa's offsets) and saved here, not written into the twin folder.
- The origin offsets come from a first RoboCasa build for the chosen style; without them (offline) the stove would
  sit 14.6 cm low again.
- No robot, task, `Kitchen` environment or rendering ran in these rooms; this is the layout and fixture builder and a
  MuJoCo compile with `mj_forward`.
- One authored room and one RoomPlan room; neither has an island, a table, an oblique wall or a non-kitchen box.
  Those paths are unit-tested offline only (`tests/test_robocasa_layout.py`).
