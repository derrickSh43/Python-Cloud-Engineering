"""Cloud provider adapters.

Everything cloud-specific that is *not* a security rule lives here: how to recognise a provider
from Terraform's provider address, which attribute holds tags/labels, and which resource types hold
data (stateful). The rest of ChangeGate asks this module instead of hard-coding cloud names, so adding
another cloud means adding one Provider entry - nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Provider:
    key: str                           # short provider name used in Terraform, e.g. "aws"
    cloud: str                         # the cloud family reported to users, e.g. "aws", "gcp"
    tag_attributes: tuple[str, ...]    # where resource metadata lives, in order of preference
    stateful_types: frozenset[str] = field(default_factory=frozenset)


AWS = Provider(
    key="aws",
    cloud="aws",
    tag_attributes=("tags_all", "tags"),   # tags_all includes provider default_tags
    stateful_types=frozenset({
        "aws_db_instance", "aws_rds_cluster", "aws_dynamodb_table", "aws_s3_bucket", "aws_ebs_volume",
        "aws_efs_file_system", "aws_elasticache_cluster", "aws_elasticache_replication_group",
        "aws_kms_key", "aws_secretsmanager_secret", "aws_redshift_cluster", "aws_opensearch_domain",
    }),
)

GOOGLE = Provider(
    key="google",
    cloud="gcp",
    tag_attributes=("labels",),
    stateful_types=frozenset({
        "google_sql_database_instance", "google_sql_database", "google_storage_bucket",
        "google_compute_disk", "google_bigquery_dataset", "google_bigquery_table",
        "google_spanner_instance", "google_spanner_database", "google_redis_instance",
        "google_filestore_instance", "google_kms_crypto_key", "google_secret_manager_secret",
    }),
)

GOOGLE_BETA = Provider(key="google-beta", cloud="gcp", tag_attributes=GOOGLE.tag_attributes,
                       stateful_types=GOOGLE.stateful_types)

_REGISTRY: dict[str, Provider] = {}


def register(provider: Provider) -> None:
    _REGISTRY[provider.key] = provider


for _p in (AWS, GOOGLE, GOOGLE_BETA):
    register(_p)


def provider_key(provider_name: str) -> str:
    """'registry.terraform.io/hashicorp/aws' -> 'aws';  'aws' -> 'aws'."""
    return provider_name.rstrip("/").rsplit("/", 1)[-1]


def lookup(provider_name: str) -> Provider | None:
    return _REGISTRY.get(provider_key(provider_name))


def cloud_for(provider_name: str) -> str:
    provider = lookup(provider_name)
    return provider.cloud if provider else "other"


def all_stateful_types() -> frozenset[str]:
    types: set[str] = set()
    for provider in _REGISTRY.values():
        types |= provider.stateful_types
    return frozenset(types)
