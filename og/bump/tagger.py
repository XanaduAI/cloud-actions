import inspect
import os
import re
import subprocess
from logging import getLogger
from operator import methodcaller
from pathlib import Path

import openai
import semver


def main():
    logger = getLogger(__name__)
    subprocess_kwargs = {
        "encoding": "utf-8",
        "stdout": subprocess.PIPE,
        "shell": True,
        "env": os.environ,
    }
    pkg_base = Path(os.getcwd())
    ver_file = min(
        [*pkg_base.glob("**/_version.py")], key=lambda path: len(path.resolve().parents)
    )
    changelog_file = min(
        [*pkg_base.glob("**/CHANGELOG.md")],
        key=lambda path: len(path.resolve().parents),
    )

    current_branch = subprocess.run(
        "git rev-parse --abbrev-ref HEAD", **subprocess_kwargs
    ).stdout.strip()
    base_branch = os.environ["BASE_BRANCH"]
    pr_body = Path("/tmp/pr_body").read_text().strip()
    pr_title = Path("/tmp/pr_title").read_text().strip()

    def bump() -> str:
        ver_re = re.compile(r".*__version__ = [\"\'](v?)(.*)[\"\']")
        leading_v, *[file_ver] = ver_re.match(
            (ver_file).read_text().replace("\n", " ")
        ).groups()

        # Get the name of the default branch
        print("Default branch is detected as: ", base_branch)
        # Get current version from _version.py on the default branch.
        _, *[base_branch_ver] = ver_re.match(
            subprocess.run(
                f"git show origin/{base_branch}:{ver_file.relative_to(pkg_base)}",
                **subprocess_kwargs,
            ).stdout.replace("\n", "")
            or '__version__ = "v0.0.0"',
        ).groups()

        commits = subprocess.run(
            f'git log {current_branch} --not {base_branch} --pretty=format:"%an" -- {ver_file.relative_to(pkg_base)}',
            **subprocess_kwargs,
        ).stdout.split()
        non_bot_commits = filter(lambda x: "bot" in x.lowercase().split(" "), commits)

        if any(non_bot_commits):
            logger.warn(
                "Detected non bot commits to the version file, skipping version bump."
            )
            return f"{leading_v}{file_ver}"
        if semver.compare(base_branch_ver, file_ver) == -1:
            logger.warn("Version already ahead of base branch, skipping version bump.")
            return f"{leading_v}{file_ver}"

        logger.info(f"{file_ver=} {base_branch_ver=}")

        base_branch_semver = semver.VersionInfo.parse(base_branch_ver)
        try:
            bump_dict = {
                "MAJOR": "bump_major",
                "MINOR": "bump_minor",
                "PATCH": "bump_patch",
            }
            bump_ver = re.findall(
                r"\[\S\] ([A-Z]+) version bump", pr_body.replace("\n", " ")
            )[0]
            logger.info(f"Calling {bump_dict[bump_ver]} using PR body")
            new_ver = methodcaller(bump_dict[bump_ver])(base_branch_semver)
        except IndexError:
            bump_dict = {
                "feat": "bump_minor",
                "fix": "bump_patch",
                "chore": "bump_patch",
            }
            bump_ver = bump_dict.get(pr_title.split(":")[0], "bump_patch")
            new_ver = methodcaller(bump_ver)(base_branch_semver)
            logger.info(f"Calling {bump_ver} using PR title")

        logger.info(f"Tagging new version: {new_ver}")
        with ver_file.open("w") as fd:
            fd.write(f'__version__ = "{leading_v}{new_ver}"')

        return f"{leading_v}{new_ver}"

    def generate_changelog(version: str) -> None:
        commits = subprocess.run(
            f'git log {current_branch} --not {base_branch} --pretty=format:"%an" -- {changelog_file.relative_to(pkg_base)}',
            **subprocess_kwargs,
        ).stdout.split()

        non_bot_commits = filter(lambda x: "bot" in x.lowercase().split(" "), commits)

        if any(non_bot_commits):
            logger.info("Non BOT commit detected, will not modify CHANGELOG.")
            return None

        base_changelog = subprocess.run(
            f"git show origin/{base_branch}:{changelog_file.relative_to(pkg_base)}",
            **subprocess_kwargs,
        ).stdout

        pr_description = pr_body.split("**Description of the Change:**")[-1].split(
            "**Version information (please select exactly one):**"
        )[0]

        if (f"# {version}") in base_changelog:
            logger.info("Changelog already up to date, skipping update.")
            return None

        openai.api_key = os.getenv("OPENAI_API_KEY")

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Summarize this text as a plain changelog entry\n\n{pr_description}",
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        ).choices[0]["text"]
        pr_number = os.environ["PR_NUMBER"]
        github_repository = os.environ["GITHUB_REPOSITORY"]

        changelog_file.write_text(
            inspect.cleandoc(
                f"""
                # {version}
                
                [#{pr_number}](https://github.com/{github_repository}/pull/{pr_number}) {response}
                
                {base_changelog}
                """
            )
        )

    generate_changelog(bump())


if __name__ == "__main__":
    main()
