import os

import pytest

import folder_paths


def test_recursive_search_returns_relative_files_and_directory_mtimes(tmp_path):
    nested = tmp_path / "one" / "two"
    nested.mkdir(parents=True)
    root_file = tmp_path / "root.safetensors"
    nested_file = nested / "nested.safetensors"
    root_file.touch()
    nested_file.touch()

    files, directories = folder_paths.recursive_search(str(tmp_path))

    assert set(files) == {
        "root.safetensors",
        os.path.join("one", "two", "nested.safetensors"),
    }
    assert set(directories) == {str(tmp_path), str(tmp_path / "one"), str(nested)}
    assert directories[str(tmp_path)] == os.path.getmtime(tmp_path)
    assert directories[str(nested)] == os.path.getmtime(nested)


def test_recursive_search_excludes_named_directories(tmp_path):
    kept = tmp_path / "kept"
    excluded = tmp_path / ".git"
    kept.mkdir()
    excluded.mkdir()
    (kept / "model.safetensors").touch()
    (excluded / "ignored.safetensors").touch()

    files, directories = folder_paths.recursive_search(str(tmp_path), excluded_dir_names=[".git"])

    assert files == [os.path.join("kept", "model.safetensors")]
    assert str(excluded) not in directories


def test_recursive_search_accepts_relative_root(tmp_path, monkeypatch):
    root = tmp_path / "models"
    nested = root / "family"
    nested.mkdir(parents=True)
    (nested / "model.safetensors").touch()
    monkeypatch.chdir(tmp_path)

    files, directories = folder_paths.recursive_search("models")

    assert files == [os.path.join("family", "model.safetensors")]
    assert set(directories) == {"models", os.path.join("models", "family")}


def test_recursive_search_follows_directory_symlinks(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "model.safetensors").touch()
    link = tmp_path / "alias"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable")

    files, directories = folder_paths.recursive_search(str(tmp_path))

    assert os.path.join("alias", "model.safetensors") in files
    assert str(link) in directories
