from changegate import providers


def test_provider_key():
    """provider_key returns the last path segment"""
    assert providers.provider_key("registry.terraform.io/hashicorp/aws") == "aws"
    assert providers.provider_key("registry.terraform.io/hashicorp/google-beta") == "google-beta"
    assert providers.provider_key("aws") == "aws"
    assert providers.provider_key("registry.terraform.io/hashicorp/google/") == "google"


def test_lookup():
    """lookup returns the registered Provider, or None"""
    assert providers.lookup("registry.terraform.io/hashicorp/aws") is providers.AWS
    assert providers.lookup("google") is providers.GOOGLE
    assert providers.lookup("registry.terraform.io/hashicorp/azurerm") is None


def test_cloud_for():
    """cloud_for gives 'aws', 'gcp' or 'other'"""
    assert providers.cloud_for("registry.terraform.io/hashicorp/aws") == "aws"
    assert providers.cloud_for("registry.terraform.io/hashicorp/google-beta") == "gcp"
    assert providers.cloud_for("registry.terraform.io/hashicorp/azurerm") == "other"


def test_all_stateful_types():
    """all_stateful_types combines every provider's stateful types into a frozenset"""
    types = providers.all_stateful_types()
    assert isinstance(types, frozenset)
    assert "aws_db_instance" in types and "google_sql_database_instance" in types
    assert "aws_instance" not in types


def test_new_provider_is_included():
    """registering a new provider makes it visible to every lookup"""
    providers.register(providers.Provider("examplecloud", "example", ("labels",), frozenset({"examplecloud_db"})))
    assert providers.cloud_for("acme/examplecloud") == "example"
    assert "examplecloud_db" in providers.all_stateful_types()
