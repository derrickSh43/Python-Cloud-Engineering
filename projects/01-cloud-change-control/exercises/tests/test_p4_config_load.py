from pathlib import Path

from changegate import config
from changegate.config import Config, ConfigError
from changegate.models import Severity
from support import EXAMPLE_CONFIG, chdir, raises, temp_dir


def test_resolve_order():
    """explicit path, then $CHANGEGATE_CONFIG, then ./changegate.toml, then None"""
    with temp_dir() as tmp:
        assert config.resolve_path("given.toml", {"CHANGEGATE_CONFIG": "env.toml"}, tmp) == Path("given.toml")
        assert config.resolve_path(None, {"CHANGEGATE_CONFIG": "env.toml"}, tmp) == Path("env.toml")
        assert config.resolve_path(None, {}, tmp) is None
        (tmp / "changegate.toml").write_text("")
        assert config.resolve_path(None, {}, tmp) == tmp / "changegate.toml"


def test_defaults_without_file():
    """no config anywhere gives Config() defaults"""
    with temp_dir() as tmp, chdir(tmp):
        assert config.load_config(None, environ={}) == Config()


def test_load_example():
    """the example config loads with its values"""
    cfg = config.load_config(EXAMPLE_CONFIG)
    assert cfg.approvals.approvers == ("alice", "bob", "carol")
    assert cfg.risk.approval_at is Severity.MEDIUM
    assert cfg.source == EXAMPLE_CONFIG.resolve()


def test_load_from_environment():
    """the path can come from the environment mapping"""
    with temp_dir() as tmp:
        path = tmp / "team.toml"
        path.write_text('[risk]\napproval_at = "high"\n')
        assert config.load_config(environ={"CHANGEGATE_CONFIG": str(path)}).risk.approval_at is Severity.HIGH


def test_errors():
    """missing files and bad TOML raise ConfigError"""
    with temp_dir() as tmp:
        error = raises(ConfigError, config.load_config, tmp / "absent.toml")
        assert "not found" in str(error)
        bad = tmp / "bad.toml"
        bad.write_text("[risk\n")
        error = raises(ConfigError, config.load_config, bad)
        assert "not valid TOML" in str(error)
