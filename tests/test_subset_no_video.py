import json
import pytest
from pathlib import Path

from arrival.export.subset import SubsetError, subset_dataset


def test_subset_rejects_dataset_without_video_features(tmp_path):
    """subset requires video features to determine resolution."""
    root = tmp_path / "datasets" / "test_sim"
    meta = root / "meta"
    meta.mkdir(parents=True)
    (meta / "info.json").write_text(json.dumps({
        "arrival_room_id": "test",
        "fps": 20,
        "features": {
            "observation.state": {"dtype": "float32", "shape": [8]},
            "action": {"dtype": "float32", "shape": [8]},
        },
        "total_episodes": 1,
    }))
    (meta / "episodes.jsonl").write_text('{"episode_index": 0, "length": 10, "arrival_family": "counter_to_sink"}\n')
    (meta / "embodiment.json").write_text('{}')

    with pytest.raises(SubsetError, match="no video features"):
        subset_dataset(root, tmp_path / "out")
