import subprocess
from unittest import mock

import pytest

from app.core.config import settings
from app.services.audio import AudioService

INJECTED = "--input-file=/etc/hosts"


@pytest.fixture
def say_service(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "PRODUCTION")
    monkeypatch.setattr(settings, "TTS_PROVIDER", "macos_say")
    return AudioService()


def test_macos_say_passes_text_on_stdin_not_argv(say_service, tmp_path):
    output_path = str(tmp_path / "out.aiff")
    with mock.patch("app.services.audio.subprocess.run") as run:
        say_service.generate_audio(INJECTED, output_path)

    run.assert_called_once()
    argv = run.call_args.args[0]
    assert argv == ["say", "-v", say_service.macos_voice, "-o", output_path, "-f", "-"]
    assert all(INJECTED not in arg for arg in argv)
    assert run.call_args.kwargs["input"] == INJECTED


def test_tts_rejects_text_over_limit(say_service, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "TTS_MAX_INPUT_CHARS", 10)
    with mock.patch.object(subprocess, "run") as run:
        with pytest.raises(ValueError, match="too long"):
            say_service.generate_audio("x" * 11, str(tmp_path / "out.aiff"))
    run.assert_not_called()
