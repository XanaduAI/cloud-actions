import os
import re
from dataclasses import dataclass

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
    if match := re.match(r".*/(.*)", full_ref):
        return match.groups()[0]

    raise ValueError(f"Cannot parse branch name from {full_ref}")


def get_branch(ctx: GitHubContext) -> str:
    if ctx.event_name == "pull_request":
        return ctx.head_ref
    elif ctx.event_name in {"push", "release"}:
        return parse_ref(ctx.ref)


def get_sc_story_ids(
    shortcut_api_token: str,
    github_server_url: str,
    github_repository: str,
    pr_number: str,
) -> set[str]:
    pr_url = f"{github_server_url}/{github_repository}/pull/{pr_number}"

    resp = requests.get(
        "https://api.app.shortcut.com/api/v3/search",
        data={"page_size": 20, "query": f"is:story and pr:{pr_url}"},
        headers={
            "Content-Type": "application/json",
            "Shortcut-Token": shortcut_api_token,
        },
    )

    resp.raise_for_status()

    return {x["id"] for x in resp.json()["stories"]["data"]}


def get_tags(ctx: GitHubContext, branch: str) -> set[str]:
    commit_sha = ctx.sha[0:7]

    if branch in {"main", "master"}:
        tags = {"latest", branch, commit_sha}
    else:
        tags = {f"{ctx.prefix}.{branch}", f"{ctx.prefix}.{commit_sha}"}

    pr_number = None
    if ctx.event_name == "pull_request":
        pr_number = ctx.event_number
    elif ctx.event_name == "push":
        pr_number_match = re.match(r".*#(\d+).*", ctx.head_commit_message, re.MULTILINE)
        if pr_number_match:
            pr_number = pr_number_match.groups()[0]

    if pr_number and ctx.shortcut_api_token:
        sc_story_ids = get_sc_story_ids(
            ctx.shortcut_api_token, ctx.server_url, ctx.repository, pr_number
        )

        tags.update(f"sc-{id}" for id in sc_story_ids)

    return tags


def write_tags_to_output(tags: set[str]) -> None:
    result = ",".join(tags)

    print(f'Generated tags "{result}".')

    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        print(f"tags={result}", file=f)


def generate_docker_image_tags():
    ctx = GitHubContext.get()
    branch = get_branch(ctx)
    tags = get_tags(ctx, branch)
    write_tags_to_output(tags)


if __name__ == "__main__":
    generate_docker_image_tags()
