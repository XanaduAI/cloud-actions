import pytest

from src.actions.generate_docker_image_tags import parse_ref


@pytest.mark.parametrize(
    "github_ref, expected",
    [
        ("refs/heads/cloud-actions-test", "cloud-actions-test"),
        ("refs/heads/main", "main"),
    ],
)
def test_parse_ref(github_ref: str, expected: str):
    """Test that ``parse_ref`` correctly parses valid ``GITHUB_REF``."""
    assert parse_ref(github_ref) == expected
