from unittest.mock import MagicMock

import pytest

from generate_docker_image_tags.action import (Context, get_pr_number,
                                               get_sc_story_ids, get_tags,
                                               main, parse_ref)


@pytest.fixture
def mock_context() -> Context:
    return Context(
        event_name="unknown",
        sha="60eee9dd65ab5ef964f540328dd04e5e7f5eab95",
        ref="refs/heads/some-branch",
        server_url="server_url",
        repository="repository",
        event_number="1",
        prefix="prefix",
        head_commit_message="head_commit_message",
        shortcut_api_token="shortcut_api_token",
    )


@pytest.fixture
def mock_pr_context() -> Context:
    return Context(
        event_name="pull_request",
        sha="60eee9dd65ab5ef964f540328dd04e5e7f5eab95",
        ref="refs/heads/some-branch",
        server_url="server_url",
        repository="repository",
        event_number="1",
        prefix="prefix",
        head_commit_message="head_commit_message",
        shortcut_api_token="shortcut_api_token",
        head_ref="refs/heads/feature-branch",
        base_ref="refs/heads/main",
    )


class TestParseRef:
    """Tests for method ``parse_ref``."""

    @pytest.mark.parametrize(
        "github_ref, expected",
        [
            ("refs/heads/cloud-action-test", "cloud-action-test"),
            ("refs/heads/main", "main"),
        ],
    )
    def test_parse_ref(self, github_ref: str, expected: str):
        """Test that ``parse_ref`` correctly parses valid ``GITHUB_REF``."""
        assert parse_ref(github_ref) == expected

    @pytest.mark.parametrize("github_ref", ["refs", "main", ""])
    def test_parse_ref_invalid(self, github_ref: str):
        """Test that ``parse_ref`` raises errors if the ref canot be parsed."""
        with pytest.raises(
            ValueError, match=rf'Cannot parse branch name from "{github_ref}"\.'
        ):
            parse_ref(github_ref)


class TestGetPrNumber:
    """Tests for method ``get_pr_number``."""

    def test_get_pr_number_unsupported_event(self, mock_context: Context):
        """Test that ``get_pr_number`` for an unsupported event returns ``None``."""
        mock_context.event_name = "other"
        assert get_pr_number(mock_context) is None

    def test_get_pr_number_pull_request(self, mock_context: Context):
        """
        Test that ``get_pr_number`` for a pull_request event returns the
        ``event_number``.
        """
        mock_context.event_name = "pull_request"
        assert get_pr_number(mock_context) == "1"

    @pytest.mark.parametrize(
        "head_commit_message, expected",
        [("foo bar #123 baz", "123"), ("nothing here", None), ("#5", "5")],
    )
    def test_get_pr_number_push(
        self, mock_context: Context, head_commit_message: str, expected: str
    ):
        """Test that ``get_pr_number`` for a push event returns the PR number found in
        the head commit message."""
        mock_context.event_name = "push"
        mock_context.head_commit_message = head_commit_message
        assert get_pr_number(mock_context) == expected


class TestGetTags:
    """Tests for method ``get_tags``."""

    def get_tags_pull_request(self, mock_pr_context: Context):
        """Test that ``get_tags`` returns the expected tags for a PR."""
        assert get_tags(mock_pr_context) == {"dev.60eee9d", "dev.feature-branch.main"}

    @pytest.mark.parametrize("branch", ["main", "master"])
    def get_tags_push_main(self, mock_context: Context, branch: str):
        """Test that ``get_tags`` returns the expected tags for a push to ``main`` or
        ``master``."""
        mock_context.event_name = "push"
        assert get_tags(mock_context) == {"latest", branch, "60eee9d"}

    def get_tags_push_branch(self, mock_context: Context):
        """Test that ``get_tags`` returns the expected tags for a push to a non-main
        branch."""
        mock_context.event_name = "push"
        assert get_tags(mock_context) == {"dev.some-branch", "dev.60eee9d"}

    def get_tags_release(self, mock_context: Context):
        """Test that ``get_tags`` returns the expected tags for a release."""
        mock_context.ref = "refs/tags/v1.0.0"
        assert get_tags(mock_context) == {"release.60eee9d", "release.v1.0.0"}

    def get_tags_unknown_event(self, mock_context: Context):
        """Test that ``get_tags`` raises an error if an unsupported event type is used."""
        mock_context.event_name = "unknown"
        with pytest.raises(
            ValueError, match=r"Unsupported event name \"unknown\", cannot get tags."
        ):
            get_tags(mock_context)


class TestGetScStoryIds:
    """Tests for method ``get_sc_story_ids``."""

    @pytest.fixture
    def patch_request_get(self, monkeypatch):
        mock_get = MagicMock()
        monkeypatch.setattr("generate_docker_image_tags.action.requests.get", mock_get)
        return mock_get

    def test_get_sc_story_ids(self, mock_context: Context, patch_request_get):
        """
        Test that ``get_sc_story_ids`` makes a correct GET request, and correctly
        parses the result.
        """
        patch_request_get.return_value = MagicMock()
        patch_request_get.return_value.json = MagicMock(
            return_value={"stories": {"data": [{"id": "12345"}, {"id": "67890"}]}}
        )

        have_story_ids = get_sc_story_ids(mock_context, "421")

        assert have_story_ids == {"12345", "67890"}

        want_pr_url = "server_url/repository/pull/421"
        patch_request_get.assert_called_once_with(
            "https://api.app.shortcut.com/api/v3/search",
            data={"page_size": 20, "query": f"is:story and pr:{want_pr_url}"},
            headers={
                "Content-Type": "application/json",
                "Shortcut-Token": "shortcut_api_token",
            },
        )

    def test_get_sc_story_ids_no_match(self, mock_context: Context, patch_request_get):
        """
        Test that ``get_sc_story_ids`` returns an empty set if no results are found.
        """
        patch_request_get.return_value = MagicMock()
        patch_request_get.return_value.json = MagicMock(
            return_value={"stories": {"data": []}}
        )

        have_story_ids = get_sc_story_ids(mock_context, "421")
        assert not have_story_ids

    def test_get_sc_story_ids_failure(self, mock_context: Context, patch_request_get):
        """
        Test that ``get_sc_story_ids`` returns an empty set if the GET request fails.
        """
        patch_request_get.side_effect = ValueError("Some request error occurred")

        have_story_ids = get_sc_story_ids(mock_context, "100")
        assert not have_story_ids


class TestMain:
    """Tests for the action ``main`` method."""

    @pytest.fixture
    def patch_get_context(self, mock_context, monkeypatch):
        mock_get_context = MagicMock(return_value=mock_context)
        monkeypatch.setattr(
            "generate_docker_image_tags.action.Context.get", mock_get_context
        )
        return mock_get_context

    @pytest.fixture
    def patch_get_sc_story_ids(self, monkeypatch):
        mock_call = MagicMock(return_value={"11111"})
        monkeypatch.setattr(
            "generate_docker_image_tags.action.get_sc_story_ids", mock_call
        )
        return mock_call

    @pytest.fixture
    def patch_write_tags_to_output(self, monkeypatch):
        mock_func = MagicMock()
        monkeypatch.setattr(
            "generate_docker_image_tags.action.write_tags_to_output", mock_func
        )
        return mock_func

    def test_pull_request(
        self,
        mock_context,
        patch_get_context,
        patch_get_sc_story_ids,
        patch_write_tags_to_output,
    ):
        """Tests the ``main`` method for ``pull_requests``."""
        mock_context.event_name = "pull_request"
        mock_context.head_ref = "refs/heads/feature-branch"
        mock_context.base_ref = "refs/heads/main"
        main()
        patch_get_context.assert_called_once()
        patch_get_sc_story_ids.assert_called_once_with(mock_context, "1")
        patch_write_tags_to_output.assert_called_once_with(
            {"dev.60eee9d", "sc-11111", "dev.feature-branch.main"}
        )

    @pytest.mark.parametrize("branch", ["main", "master"])
    def test_push_to_main(
        self,
        mock_context,
        branch,
        patch_get_context,
        patch_get_sc_story_ids,
        patch_write_tags_to_output,
    ):
        """Tests the ``main`` method for ``push`` to ``main``/``master``."""
        mock_context.event_name = "push"
        mock_context.ref = f"refs/heads/{branch}"
        mock_context.head_commit_message = "Merged PR #1 !!!"
        main()
        patch_get_context.assert_called_once()
        patch_get_sc_story_ids.assert_called_once_with(mock_context, "1")
        patch_write_tags_to_output.assert_called_once_with(
            {"latest", branch, "60eee9d", "sc-11111"}
        )

    def test_push_to_branch(
        self,
        mock_context,
        patch_get_context,
        patch_get_sc_story_ids,
        patch_write_tags_to_output,
    ):
        """Tests the ``main`` method for ``push`` to a non-main branch."""
        mock_context.event_name = "push"
        mock_context.head_commit_message = "Merged PR #2 !!!"
        main()
        patch_get_context.assert_called_once()
        patch_get_sc_story_ids.assert_called_once_with(mock_context, "2")
        patch_write_tags_to_output.assert_called_once_with(
            {"dev.some-branch", "dev.60eee9d", "sc-11111"}
        )

    def test_release(
        self,
        mock_context,
        patch_get_context,
        patch_get_sc_story_ids,
        patch_write_tags_to_output,
    ):
        """Tests the ``main`` method for ``release`` events."""
        mock_context.event_name = "release"
        main()
        patch_get_context.assert_called_once()
        patch_write_tags_to_output.assert_called_once_with(
            {"release.some-branch", "release.60eee9d"}
        )
