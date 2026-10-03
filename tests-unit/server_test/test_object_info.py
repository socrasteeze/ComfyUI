import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import folder_paths
import nodes
import server


@pytest.mark.parametrize("path", ["/object_info", "/object_info/{node_class}"])
def test_object_info_reads_legacy_inputs_once(monkeypatch, tmp_path, path):
    class ModelLoader:
        RETURN_TYPES = ("MODEL",)

        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"model": (["model.safetensors"],)}, "optional": {"strength": ("FLOAT",)}}

    inputs = MagicMock(side_effect=ModelLoader.INPUT_TYPES)
    monkeypatch.setattr(ModelLoader, "INPUT_TYPES", inputs)
    monkeypatch.setattr(nodes, "NODE_CLASS_MAPPINGS", {"ModelLoader": ModelLoader})
    monkeypatch.setattr(folder_paths, "user_directory", str(tmp_path))
    monkeypatch.setattr(server.args, "front_end_root", str(tmp_path))
    monkeypatch.setattr(server.PromptServer, "instance", None, raising=False)
    prompt_server = server.PromptServer(None, MagicMock(enabled=False))
    handler = next(route.handler for route in prompt_server.routes if route.path == path)

    response = asyncio.run(handler(SimpleNamespace(match_info={"node_class": "ModelLoader"})))
    info = json.loads(response.body)["ModelLoader"]

    inputs.assert_called_once_with()
    assert info["input"] == {"required": {"model": [["model.safetensors"]]}, "optional": {"strength": ["FLOAT"]}}
    assert info["input_order"] == {"required": ["model"], "optional": ["strength"]}
    assert info["output"] == ["MODEL"]
