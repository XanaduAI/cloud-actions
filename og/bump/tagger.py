import os
import re
import subprocess
from operator import methodcaller
from pathlib import Path

import semver

if __name__ == "__main__":
    # Parse version file (Cannot import relative boo)
    pkg_base = Path(os.getcwd())
    ver_file = pkg_base / pkg_base.name.replace("-", "_") / "_version.py"
    ver_re = re.compile(r".*__version__ = \"(v?)(.*)\"")
    leading_v, *[file_ver] = ver_re.match((ver_file).read_text()).groups()

    subprocess_kwargs = {
        "encoding": "utf-8",
        "stdout": subprocess.PIPE,
        "shell": True,
        "env": os.environ,
    }
    # Get the name of the default branch
    default_branch = os.environ["DEFAULT_BRANCH"]
    print("Default branch is detected as: ", default_branch)
    # Get current version from _version.py on the default branch.
    _, *[default_branch_ver] = ver_re.match(
        subprocess.run(
            f"git show {default_branch}:{pkg_base.name.replace('-', '_')}/_version.py",
            **subprocess_kwargs,
        ).stdout.split('\n')[-1]
    ).groups()
    # If version not updated in file
    if semver.compare(default_branch_ver, file_ver) != -1:
        print(f"{file_ver=} {default_branch_ver=}")

        default_branch_semver = semver.VersionInfo.parse(default_branch_ver)
        try:
            pr_body = os.environ["PR_BODY"]
            bump_dict = {
                "MAJOR": "bump_major",
                "MINOR": "bump_minor",
                "PATCH": "bump_patch",
            }
            bump_ver = re.findall(
                r"\[\S\] ([A-Z]+) version bump", pr_body.replace("\n", " ")
            )[0]
            print(f"Calling {bump_dict[bump_ver]} using PR body")
            new_ver = methodcaller(bump_dict[bump_ver])(default_branch_semver)
        except IndexError:
            pr_title = os.environ["PR_TITLE"]
            bump_dict = {
                "feat": "bump_minor",
                "fix": "bump_patch",
                "chore": "bump_patch",
            }
            bump_ver = bump_dict.get(pr_title.split(":")[0], "bump_patch")
            new_ver = methodcaller(bump_ver)(default_branch_semver)
            print(f"Calling {bump_ver} using PR title")

        print(f"Tagging new version: {new_ver}")
        with ver_file.open("w") as fd:
            fd.write(f'__version__ = "{leading_v}{new_ver}"')
