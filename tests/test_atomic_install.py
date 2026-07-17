from __future__ import annotations

import os

import pytest

from free_agent_md.update import _install_outputs


def test_interrupted_output_install_rolls_back_every_target(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root"
    stage = tmp_path / "stage"
    root.mkdir()
    stage.mkdir()
    outputs = ("README.md", "ARCHIVE.md")
    (root / "README.md").write_text("old readme", encoding="utf-8")
    (root / "ARCHIVE.md").write_text("old archive", encoding="utf-8")
    (stage / "README.md").write_text("new readme", encoding="utf-8")
    (stage / "ARCHIVE.md").write_text("new archive", encoding="utf-8")

    real_replace = os.replace

    def interrupted(source, destination):
        if source == stage / "ARCHIVE.md":
            raise OSError("simulated write interruption")
        return real_replace(source, destination)

    monkeypatch.setattr("free_agent_md.update.os.replace", interrupted)
    with pytest.raises(OSError, match="interruption"):
        _install_outputs(root, stage, outputs)

    assert (root / "README.md").read_text(encoding="utf-8") == "old readme"
    assert (root / "ARCHIVE.md").read_text(encoding="utf-8") == "old archive"
