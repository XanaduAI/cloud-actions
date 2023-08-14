import os
import re
import subprocess
from logging import getLogger
from operator import methodcaller
from pathlib import Path

import semver

logger = getLogger(__name__)

pkg_base = Path(os.getcwd())
subprocess_kwargs = {
    "encoding": "utf-8",
    "stdout": subprocess.PIPE,
    "shell": True,
    "env": os.environ,
    "cwd": pkg_base,
}

current_branch = subprocess.run(
    "git rev-parse --abbrev-ref HEAD", **subprocess_kwargs
).stdout.strip()
base_branch = os.environ["BASE_BRANCH"]
pr_body = Path("/tmp/pr_body").read_text().strip()
pr_title = Path("/tmp/pr_title").read_text().strip()


def bump() -> str:
    """Update the version file and return the version number.

    This function will update the version file only and only if the file was not
    touched by anyone other than the bot going back as far as base branch. Always
    returns the head (semantic) version.

    To figure out how much to bump the version, this function will first try to
    parse the PR description body, looking for checkboxes checked that match the
    OG standard pattern.
    If that fails, it will try SC format for the PR title prefix.
    If that also fails, it will bump the PATCH version.

    Returns:
        str: Semantic version of HEAD.
    """
    ver_file = min(
        [*pkg_base.glob("**/_version.py")], key=lambda path: len(path.resolve().parents)
    )
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

    # Get a list of users who have made a commit touching the version file in the current branch.
    committers = subprocess.run(
        f'git log {current_branch} --not origin/{base_branch} --pretty=format:"%an" -- {ver_file.relative_to(pkg_base)}',
        **subprocess_kwargs,
    ).stdout.split("\n")

    # Filter the committer list by who has "bot" in their name as a separate word
    non_bot_committers = filter(lambda x: "bot" not in x.lower().split(" "), committers)

    if any(non_bot_committers) and semver.compare(base_branch_ver, file_ver) == -1:
        logger.warn(
            "Detected non bot commits to the version file, skipping version bump."
        )
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
    ver_file.write_text(f'__version__ = "{leading_v}{new_ver}"\n')

    return f"{leading_v}{new_ver}"


def generate_changelog(version: str) -> None:
    """This function takes the version string from `bump` function, and formats the
    relevant PR description section to prepend the CHANGELOG.md with.

    This function will update the CHANGELOG file only and only if the file was not
    touched by anyone other than the bot going back as far as base branch.

    Args:
        version (str): Semantic version to tag the CHANGELOG entry with.
    """
    # Get a list of users who have made a commit touching the changelog file in the current branch
    if changelog_file := os.environ.get("CHANGELOG_PATH", "").strip():
        changelog_file = Path(changelog_file).resolve()
    else:
        try:
            changelog_file = min(
                [*pkg_base.glob("**/CHANGELOG.md")],
                key=lambda path: len(path.resolve().parents),
            )
        except ValueError:
            changelog_file = pkg_base / "CHANGELOG.md"

    if not changelog_file.is_file():
        changelog_file.touch()

    committers = subprocess.run(
        f'git log {current_branch} --not origin/{base_branch} --pretty=format:"%an" -- {changelog_file.relative_to(pkg_base)}',
        **subprocess_kwargs,
    ).stdout.split("\n")

    # Filter the committer list by who has "bot" in their name as a separate word
    non_bot_committers = filter(lambda x: "bot" not in x.lower().split(" "), committers)

    # Check if the changelog file is identical (ignoring whitespace) to the base_branch changelog
    changelog_was_modified = bool(
        subprocess.run(
            f"git diff origin/{base_branch} --ignore-blank-lines -w -s --exit-code -- {changelog_file.relative_to(pkg_base)}",
            **subprocess_kwargs,
        ).returncode
    )

    if any(non_bot_committers) and changelog_was_modified:
        logger.info("Non BOT commit detected, will not modify CHANGELOG.")
        line = next(
            filter(
                lambda line: not line.isspace() and bool(line),
                changelog_file.read_text().splitlines(),
            )
        )
        if version not in (changelog_version := line.removeprefix("# ")):
            raise RuntimeError(
                f"Unexpected version in CHANGELOG. Expected {version}, got {changelog_version}."
            )

        return None

    base_changelog = subprocess.run(
        f"git show origin/{base_branch}:{changelog_file.relative_to(pkg_base)}",
        **subprocess_kwargs,
    ).stdout

    pr_description = (
        pr_body.split("**Description of the Change:**")[-1]
        .split("**Version information (please select exactly one):**")[0]
        .strip()
    )
    reg = re.compile(r"\#\s?v?\d+\.\d+\.\d+")
    changelog = {
        k: v.strip()
        for k, v in zip(
            re.findall(reg, base_changelog), re.split(reg, base_changelog)[1:]
        )
    }

    pr_number = os.environ["PR_NUMBER"]
    github_repository = os.environ["GITHUB_REPOSITORY"]
    version = os.environ["VERSION_TEMPLATE"].strip().format(version)

    if pr_description != changelog_file[f"# {version}"]:
        changelog[
            f"# {version}"
        ] = f"[#{pr_number}](https://github.com/{github_repository}/pull/{pr_number}) {pr_description}\n\n{base_changelog}"

    changelog_file.write_text(
        "\n\n".join(
            [
                f"{version}\n\n{changelog[version]}"
                for version in sorted(changelog.keys(), reverse=True)
            ]
        )
    )


if __name__ == "__main__":
    generate_changelog(bump())
