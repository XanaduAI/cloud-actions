import os
import re
from dataclasses import dataclass
from typing import Optional

import requests

from src.lib.github_context import GitHubContext


@dataclass
class Context(GitHubContext):
    event_number: str
    prefix: str
    head_commit_message: str
    shortcut_api_token: str

    @classmethod
    def get(cls) -> "Context":
        base = GitHubContext.get()
        return cls(
            event_number=os.environ["INPUT_EVENT_NUMBER"],
            prefix=os.environ["INPUT_PREFIX"],
            head_commit_message=os.environ["INPUT_HEAD_COMMIT_MESSAGE"],
            shortcut_api_token=os.environ["INPUT_SHORTCUT_API_TOKEN"],
            **base,
        )


def parse_ref(full_ref: str) -> str:
    """
    Parses a ref to return the right-most part of the path.

    Example: ``refs/heads/main`` -> ``main``
    """
    if match := re.match(r".*/(.*)", full_ref):
        return match.groups()[0]

    raise ValueError(f'Cannot parse branch name from "{full_ref}".')


def get_pr_number(ctx: Context) -> Optional[str]:
    """
    Gets the PR number from the context, or ``None``.

    pull_request: returns the ``event_number``
    push: searches for "#<PR_NUMBER>" inside the ``head_commit_message``.
    """
    if ctx.event_name == "pull_request":
        return ctx.event_number

    if ctx.event_name == "push":
        match = re.match(r".*#(\d+).*", ctx.head_commit_message, re.MULTILINE)
        if match:
            return match.groups()[0]

    return None


def get_tags(ctx: Context) -> set[str]:
    """
    Gets the tags from the context depending on the ``event_name``:

    ``push``:
        to main/master: ``latest``, ``<sha>``, ``<ref>``
        to other branch: ``dev.<sha>``, ``dev.<ref>``
    ``release``: ``release.<sha>`` ``release.<ref>``
    ``pull_request``: ``dev.<sha>`` ``dev.<head_ref>.<base_ref>``
    """
    sha = ctx.sha[0:7]

    if ctx.event_name == "pull_request":
        to_ref = parse_ref(ctx.base_ref)
        from_ref = parse_ref(ctx.head_ref)
        return {f"dev.{sha}", f"dev.{from_ref}.{to_ref}"}

    if ctx.event_name == "release":
        ref = parse_ref(ctx.ref)
        return {f"release.{sha}", f"release.{ref}"}

    if ctx.event_name == "push":
        ref = parse_ref(ctx.ref)
        if ref in {"main", "master"}:
            return {sha, "latest", ref}
        else:
            return {f"dev.{sha}", f"dev.{ref}"}

    raise ValueError(f'Unsupported event name "{ctx.event_name}", cannot get tags.')


def get_sc_story_ids(
    ctx: Context,
    pr_number: str,
) -> set[str]:
    """Searches ``shortcut`` for stories that refer to the given PR, and returns the ids
    of the matching stories."""
    pr_url = f"{ctx.server_url}/{ctx.repository}/pull/{pr_number}"

    try:
        resp = requests.get(
            "https://api.app.shortcut.com/api/v3/search",
            data={"page_size": 20, "query": f"is:story and pr:{pr_url}"},
            headers={
                "Content-Type": "application/json",
                "Shortcut-Token": ctx.shortcut_api_token,
            },
        )
        resp.raise_for_status()
    except:
        return {}

    return {x["id"] for x in resp.json()["stories"]["data"]}


def write_tags_to_output(tags: set[str]) -> None:
    """Writes ``tags`` to the output of the GitHub Action."""
    result = ",".join(tags)

    print(f'Generated tags "{result}".')

    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        print(f"tags={result}", file=f)


def main():
    """Main entrypoint for the action."""
    ctx = Context.get()
    tags = get_tags(ctx)

    pr_number = get_pr_number(ctx)
    if pr_number and ctx.shortcut_api_token:
        sc_story_ids = get_sc_story_ids(ctx, pr_number)
        tags.update(f"sc-{id}" for id in sc_story_ids)

    write_tags_to_output(tags)


if __name__ == "__main__":
    main()
