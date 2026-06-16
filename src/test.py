"""Tests for runner lifecycle management."""

from unittest.mock import MagicMock, patch

import pytest

try:
    from src.main import (
        RunnerConfig,
        RunnerError,
        configure_runner,
        get_runner_url,
        unregister_runner,
    )
except ModuleNotFoundError:
    from main import (  # type: ignore
        RunnerConfig,
        RunnerError,
        configure_runner,
        get_runner_url,
        unregister_runner,
    )


class TestRunnerConfig:
    def test_config_dataclass(self):
        config = RunnerConfig(
            owner="myorg",
            repo="myrepo",
            token="TOKEN123",
            labels=["aws", "linux"],
            name="runner-01",
        )
        assert config.owner == "myorg"
        assert config.repo == "myrepo"
        assert config.labels == ["aws", "linux"]


class TestGetRunnerUrl:
    def test_explicit_version(self):
        url = get_runner_url("2.316.1")
        assert "v2.316.1" in url
        assert "actions-runner" in url
        assert "/releases/download/v2.316.1/" in url
        assert "/releases/tag/" not in url

    def test_resolves_latest_when_no_version(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__ = MagicMock(
                return_value=MagicMock(
                    read=MagicMock(
                        return_value=(
                            b'{"tag_name": "v2.317.0", "html_url": '
                            b'"https://github.com/actions/runner/releases/tag/v2.317.0"}'
                        )
                    )
                )
            )
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response

            url = get_runner_url(None)
            assert "v2.317.0" in url
            assert "/releases/download/v2.317.0/" in url
            assert "/releases/tag/" not in url


class TestConfigureRunner:
    def test_config_sh_not_found_raises(self, tmp_path):
        config = RunnerConfig(
            owner="org", repo="repo", token="tok", labels=[], name="r1"
        )
        with pytest.raises(RunnerError, match="config.sh not found"):
            configure_runner(tmp_path, config)

    def test_config_sh_failure_raises(self, tmp_path):
        runner_dir = tmp_path / "actions-runner"
        runner_dir.mkdir()
        config_sh = runner_dir / "config.sh"
        config_sh.write_text("#!/bin/sh\nexit 1\n")
        config_sh.chmod(0o755)

        config = RunnerConfig(
            owner="org", repo="repo", token="tok", labels=[], name="r1"
        )
        with pytest.raises(RunnerError, match="config.sh failed"):
            configure_runner(runner_dir, config)


class TestUnregisterRunner:
    def test_remove_sh_not_found_raises(self, tmp_path):
        with pytest.raises(RunnerError, match="remove.sh not found"):
            unregister_runner(tmp_path, "token", "runner-1")

    def test_remove_sh_failure_is_logged_not_raised(self, tmp_path, caplog):
        runner_dir = tmp_path / "actions-runner"
        runner_dir.mkdir()
        bin_dir = runner_dir / "bin"
        bin_dir.mkdir()
        remove_sh = bin_dir / "remove.sh"
        remove_sh.write_text("#!/bin/sh\nexit 1\n")
        remove_sh.chmod(0o755)

        # Should not raise -- failures are logged, not propagated.
        unregister_runner(runner_dir, "token", "runner-1")
        assert "remove.sh exited" in caplog.text
