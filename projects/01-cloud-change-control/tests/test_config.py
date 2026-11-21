import pytest

from changegate import config as cfg
from changegate.config import ConfigError
from changegate.models import Severity


def test_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(cfg.CONFIG_ENV, raising=False)
    config = cfg.load_config()
    assert config.source is None
    assert config.risk.approval_at is Severity.MEDIUM and config.risk.block_at is Severity.CRITICAL
    assert config.approvals.approvers == ()


def test_example_config_loads(example_config_path):
    config = cfg.load_config(example_config_path)
    assert config.approvals.approvers == ("alice", "bob", "carol")
    assert config.approvals.required_for(Severity.HIGH) == 2
    assert config.policies.settings["CG-REQUIRED-TAGS"]["required"] == ["owner", "environment"]
    # relative audit path resolves next to the config file
    assert config.audit.path.parent == example_config_path.parent.resolve()


def test_env_var_and_cwd_lookup(tmp_path, monkeypatch):
    (tmp_path / "custom.toml").write_text('[risk]\napproval_at = "high"\n')
    monkeypatch.setenv(cfg.CONFIG_ENV, str(tmp_path / "custom.toml"))
    assert cfg.load_config().risk.approval_at is Severity.HIGH
    monkeypatch.delenv(cfg.CONFIG_ENV)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "changegate.toml").write_text('[risk]\napproval_at = "low"\n')
    assert cfg.load_config().risk.approval_at is Severity.LOW


@pytest.mark.parametrize("data, message", [
    ({"risks": {}}, "unknown setting"),
    ({"risk": {"aproval_at": "high"}}, "unknown setting"),
    ({"risk": {"approval_at": "severe"}}, "unknown severity"),
    ({"risk": {"approval_at": "high", "block_at": "medium"}}, "must not be lower"),
    ({"risk": {"destructive_escalation_threshold": -1}}, ">= 0"),
    ({"approvals": {"required": {"high": 0}}}, ">= 1"),
    ({"approvals": {"approvers": "alice"}}, "list of strings"),
    ({"approvals": {"max_age_hours": 0}}, "positive"),
    ({"approvals": {"allow_self_approval": "yes"}}, "true or false"),
    ({"policies": {"settings": {"X": 1}}}, "must be a table"),
    ({"audit": {"enabled": "no"}}, "true or false"),
])
def test_invalid_config(data, message):
    with pytest.raises(ConfigError, match=message):
        cfg.from_dict(data)


def test_block_never():
    assert cfg.from_dict({"risk": {"block_at": "never"}}).risk.block_at is None


def test_bad_toml(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("[risk\n")
    with pytest.raises(ConfigError, match="not valid TOML"):
        cfg.load_config(bad)


def test_missing_explicit_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        cfg.load_config(tmp_path / "absent.toml")
