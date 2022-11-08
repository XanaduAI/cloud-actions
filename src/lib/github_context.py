import os
from dataclasses import dataclass


@dataclass
class GitHubContext:
    event_name: str
    sha: str
    head_ref: str
    ref: str
    server_url: str
    repository: str
    event_number: str
    prefix: str
    head_commit_message: str
    shortcut_api_token: str

    @classmethod
    def get(cls) -> "GitHubContext":
        return cls(
            event_name=os.environ["GITHUB_EVENT_NAME"],
            sha=os.environ["GITHUB_SHA"],
            head_ref=os.environ["GITHUB_HEAD_REF"],
            ref=os.environ["GITHUB_REF"],
            server_url=os.environ["GITHUB_SERVER_URL"],
            repository=os.environ["GITHUB_REPOSITORY"],
            event_number=os.environ["INPUT_EVENT_NUMBER"],
            prefix=os.environ["INPUT_PREFIX"],
            head_commit_message=os.environ["INPUT_HEAD_COMMIT_MESSAGE"],
            shortcut_api_token=os.environ["INPUT_SHORTCUT_API_TOKEN"],
        )
