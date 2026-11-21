"""Regenerates the sample Terraform plans in sample_data/plans/.

The plans follow the structure of `terraform show -json` (format_version 1.2) for the AWS
(hashicorp/aws) and Google (hashicorp/google) providers, trimmed to the attributes ChangeGate reads.
All identifiers are placeholders (account 123456789012, project example-project); nothing here refers
to real infrastructure. Run:  python sample_data/build_samples.py
"""

import json
from pathlib import Path

OUT = Path(__file__).parent / "plans"
AWS = "registry.terraform.io/hashicorp/aws"
GOOGLE = "registry.terraform.io/hashicorp/google"
ACCOUNT = "123456789012"
PROJECT = "example-project"
TAGS = {"owner": "platform-team", "environment": "dev"}
LABELS = {"owner": "platform-team", "environment": "dev"}


def rc(address_type, name, provider, actions, before=None, after=None, after_unknown=None, mode="managed"):
    prefix = "data." if mode == "data" else ""
    return {
        "address": "%s%s.%s" % (prefix, address_type, name), "mode": mode, "type": address_type, "name": name,
        "provider_name": provider,
        "change": {"actions": actions, "before": before, "after": after, "after_unknown": after_unknown or {},
                   "before_sensitive": False if before is None else {},
                   "after_sensitive": False if after is None else {}},
    }


def plan(changes, terraform_version="1.9.5"):
    return {"format_version": "1.2", "terraform_version": terraform_version,
            "planned_values": {"root_module": {}}, "resource_changes": changes,
            "configuration": {"root_module": {}}, "timestamp": "2026-01-15T10:00:00Z",
            "applyable": True, "complete": True, "errored": False}


def sg(name, ingress, tags=TAGS):
    return {"name": name, "description": "managed by terraform", "vpc_id": "vpc-0example", "ingress": ingress,
            "egress": [], "tags": tags, "tags_all": tags}


def ingress(port_from, port_to, cidrs, protocol="tcp", description=""):
    return {"from_port": port_from, "to_port": port_to, "protocol": protocol, "cidr_blocks": cidrs,
            "ipv6_cidr_blocks": [], "description": description, "prefix_list_ids": [], "security_groups": [],
            "self": False}


def iam_doc(statements):
    return json.dumps({"Version": "2012-10-17", "Statement": statements})


SAMPLES = {}

SAMPLES["aws_safe.json"] = plan([
    rc("aws_s3_bucket", "logs", AWS, ["create"], None,
       {"bucket": "example-app-logs", "force_destroy": False, "tags": TAGS, "tags_all": TAGS},
       {"arn": True, "id": True}),
    rc("aws_s3_bucket_public_access_block", "logs", AWS, ["create"], None,
       {"block_public_acls": True, "block_public_policy": True, "ignore_public_acls": True,
        "restrict_public_buckets": True}, {"bucket": True, "id": True}),
    rc("aws_security_group", "web", AWS, ["create"], None,
       sg("web", [ingress(443, 443, ["0.0.0.0/0"], description="https")]), {"id": True, "arn": True}),
    rc("aws_instance", "app", AWS, ["update"],
       {"ami": "ami-0example", "instance_type": "t3.micro", "tags": {"owner": "platform-team"},
        "tags_all": {"owner": "platform-team"}, "root_block_device": [{"encrypted": True, "volume_size": 20}]},
       {"ami": "ami-0example", "instance_type": "t3.micro", "tags": TAGS, "tags_all": TAGS,
        "root_block_device": [{"encrypted": True, "volume_size": 20}]}),
    rc("aws_caller_identity", "current", AWS, ["read"], None, {"account_id": ACCOUNT}, mode="data"),
])

SAMPLES["aws_risky.json"] = plan([
    rc("aws_s3_bucket_acl", "assets", AWS, ["create"], None, {"bucket": "example-public-assets", "acl": "public-read"}),
    rc("aws_s3_bucket_public_access_block", "assets", AWS, ["create"], None,
       {"block_public_acls": False, "block_public_policy": False, "ignore_public_acls": True,
        "restrict_public_buckets": True}),
    rc("aws_security_group", "admin", AWS, ["create"], None,
       sg("admin", [ingress(22, 22, ["0.0.0.0/0"], description="ssh"), ingress(443, 443, ["10.0.0.0/8"])]),
       {"id": True}),
    rc("aws_iam_policy", "deploy", AWS, ["create"], None,
       {"name": "deploy-everything", "policy": iam_doc([{"Sid": "Everything", "Effect": "Allow", "Action": "*",
                                                         "Resource": "*"}])}),
    rc("aws_ebs_volume", "data", AWS, ["create"], None,
       {"availability_zone": "us-east-1a", "size": 100, "encrypted": False, "tags": TAGS, "tags_all": TAGS}),
    rc("aws_db_instance", "orders", AWS, ["create"], None,
       {"identifier": "orders", "engine": "postgres", "instance_class": "db.t3.micro", "storage_encrypted": False,
        "publicly_accessible": True, "tags": TAGS, "tags_all": TAGS}, {"endpoint": True}),
])

SAMPLES["aws_db_replace.json"] = plan([
    rc("aws_db_instance", "orders", AWS, ["delete", "create"],
       {"identifier": "orders", "engine": "postgres", "engine_version": "15.4", "storage_encrypted": True,
        "publicly_accessible": False, "tags": TAGS, "tags_all": TAGS},
       {"identifier": "orders", "engine": "postgres", "engine_version": "16.1", "storage_encrypted": True,
        "publicly_accessible": False, "tags": TAGS, "tags_all": TAGS}, {"endpoint": True, "id": True}),
    rc("aws_security_group_rule", "db_from_app", AWS, ["create"], None,
       {"type": "ingress", "from_port": 5432, "to_port": 5432, "protocol": "tcp", "cidr_blocks": ["10.0.1.0/24"],
        "security_group_id": "sg-0example"}),
])

SAMPLES["gcp_safe.json"] = plan([
    rc("google_storage_bucket", "reports", GOOGLE, ["create"], None,
       {"name": "example-project-reports", "location": "US", "project": PROJECT, "uniform_bucket_level_access": True,
        "public_access_prevention": "enforced", "labels": LABELS, "force_destroy": False},
       {"self_link": True, "url": True}),
    rc("google_storage_bucket_iam_member", "reports_reader", GOOGLE, ["create"], None,
       {"bucket": "example-project-reports", "role": "roles/storage.objectViewer",
        "member": "serviceAccount:reporter@example-project.iam.gserviceaccount.com"}),
    rc("google_compute_firewall", "allow_https", GOOGLE, ["create"], None,
       {"name": "allow-https", "network": "default", "project": PROJECT, "direction": "INGRESS",
        "source_ranges": ["0.0.0.0/0"], "allow": [{"protocol": "tcp", "ports": ["443"]}], "disabled": False}),
    rc("google_compute_instance", "app", GOOGLE, ["update"],
       {"name": "app", "machine_type": "e2-small", "labels": {"owner": "platform-team"}},
       {"name": "app", "machine_type": "e2-small", "labels": LABELS}),
])

SAMPLES["gcp_risky.json"] = plan([
    rc("google_compute_firewall", "allow_ssh", GOOGLE, ["create"], None,
       {"name": "allow-ssh", "network": "default", "project": PROJECT, "direction": "INGRESS",
        "source_ranges": ["0.0.0.0/0"], "allow": [{"protocol": "tcp", "ports": ["22", "8080-8090"]}],
        "disabled": False}),
    rc("google_compute_firewall", "allow_everything", GOOGLE, ["create"], None,
       {"name": "allow-everything", "network": "default", "project": PROJECT, "direction": "INGRESS",
        "source_ranges": ["0.0.0.0/0"], "allow": [{"protocol": "all", "ports": []}], "disabled": False}),
    rc("google_storage_bucket_iam_member", "public_read", GOOGLE, ["create"], None,
       {"bucket": "example-project-site", "role": "roles/storage.objectViewer", "member": "allUsers"}),
    rc("google_project_iam_member", "contractor_owner", GOOGLE, ["create"], None,
       {"project": PROJECT, "role": "roles/owner", "member": "user:contractor@example.com"}),
    rc("google_sql_database_instance", "main", GOOGLE, ["create"], None,
       {"name": "main", "database_version": "POSTGRES_15", "project": PROJECT, "region": "us-central1",
        "settings": [{"tier": "db-f1-micro", "ip_configuration": [{"ipv4_enabled": True, "authorized_networks": [
            {"name": "anywhere", "value": "0.0.0.0/0"}]}], "user_labels": LABELS}]}),
    rc("google_storage_bucket", "legacy", GOOGLE, ["create"], None,
       {"name": "example-project-legacy", "location": "US", "project": PROJECT,
        "uniform_bucket_level_access": False, "public_access_prevention": "inherited", "labels": LABELS}),
])

SAMPLES["gcp_bucket_acls.json"] = plan([
    rc("google_storage_bucket", "uploads", GOOGLE, ["create"], None,
       {"name": "example-project-uploads", "location": "US", "project": PROJECT,
        "uniform_bucket_level_access": False, "public_access_prevention": "enforced", "labels": LABELS}),
])

SAMPLES["multi_cloud_teardown.json"] = plan([
    rc("aws_instance", "worker_%d" % n, AWS, ["delete"],
       {"ami": "ami-0example", "instance_type": "t3.micro", "tags": TAGS, "tags_all": TAGS}, None)
    for n in range(1, 4)
] + [
    rc("google_compute_instance", "batch_%d" % n, GOOGLE, ["delete"],
       {"name": "batch-%d" % n, "machine_type": "e2-small", "labels": LABELS}, None)
    for n in range(1, 3)
] + [
    rc("aws_s3_bucket", "scratch", AWS, ["no-op"],
       {"bucket": "example-scratch", "tags": TAGS, "tags_all": TAGS},
       {"bucket": "example-scratch", "tags": TAGS, "tags_all": TAGS}),
])

SAMPLES["no_changes.json"] = plan([
    rc("aws_s3_bucket", "logs", AWS, ["no-op"],
       {"bucket": "example-app-logs", "tags": TAGS, "tags_all": TAGS},
       {"bucket": "example-app-logs", "tags": TAGS, "tags_all": TAGS}),
])

SAMPLES["missing_tags.json"] = plan([
    rc("aws_s3_bucket", "untagged", AWS, ["create"], None,
       {"bucket": "example-untagged", "tags": {"owner": "platform-team"}, "tags_all": {"owner": "platform-team"}}),
    rc("google_storage_bucket", "unlabelled", GOOGLE, ["create"], None,
       {"name": "example-project-unlabelled", "location": "US", "project": PROJECT,
        "uniform_bucket_level_access": True, "public_access_prevention": "enforced", "labels": {}}),
])


def main():
    OUT.mkdir(exist_ok=True)
    for name, data in SAMPLES.items():
        (OUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
