from changegate.policies.aws import RdsPubliclyAccessible, UnencryptedStorage
from support import make_change, messages


def run(policy, change):
    return list(policy.check(change)) if policy.applies_to(change) else []


def test_ebs_and_databases():
    """unencrypted volumes and databases are reported with the flag and value"""
    assert messages(run(UnencryptedStorage(), make_change("aws_ebs_volume", {"encrypted": False}))) == ["encrypted is False"]
    assert messages(run(UnencryptedStorage(), make_change("aws_ebs_volume", {}))) == ["encrypted is None"]
    assert messages(run(UnencryptedStorage(), make_change("aws_db_instance", {"storage_encrypted": False}))) == [
        "storage_encrypted is False"]
    assert run(UnencryptedStorage(), make_change("aws_rds_cluster", {"storage_encrypted": True})) == []


def test_unknown_flag_skipped():
    """a flag Terraform can't know yet is not reported"""
    change = make_change("aws_ebs_volume", {"encrypted": None}, unknown={"encrypted": True})
    assert run(UnencryptedStorage(), change) == []


def test_instance_volumes():
    """instance root and EBS block devices are checked"""
    change = make_change("aws_instance", {"root_block_device": [{"encrypted": False}],
                                          "ebs_block_device": [{"encrypted": True}, {"encrypted": False}]})
    assert messages(run(UnencryptedStorage(), change)) == ["root volume is not encrypted",
                                                           "EBS block device 2 is not encrypted"]
    assert run(UnencryptedStorage(), make_change("aws_instance", {"root_block_device": []})) == []
    assert run(UnencryptedStorage(), make_change("aws_instance", {"root_block_device": [{"encrypted": None}]})) == []


def test_public_database():
    """publicly_accessible = true is reported; false or missing is fine"""
    assert messages(run(RdsPubliclyAccessible(), make_change("aws_db_instance", {"publicly_accessible": True}))) == [
        "publicly_accessible = true"]
    assert run(RdsPubliclyAccessible(), make_change("aws_db_instance", {"publicly_accessible": False})) == []
    assert run(RdsPubliclyAccessible(), make_change("aws_db_instance", {})) == []
