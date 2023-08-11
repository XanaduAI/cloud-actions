import os
import subprocess
from pathlib import Path

ignore_files = set()

if (ignore_file := Path("./.lintignore")).isfile():
    ignore_paths = ignore_file.read_text().split()
    for path in ignore_paths:
        ignore_files.update(path.rglob("*"))

edited_py_files = {
    _file
    for file in subprocess(
        f"git diff origin/{os.environ['BASE_BRANCH']} --diff-filter=MAC --name-only",
        shell=True,
        stdout=subprocess.PIPE,
    ).stdout.split()
    if (_file := Path(file).resolve()).suffix == ".py"
}

files_to_format = edited_py_files - ignore_files

if files_to_format := " ".join(files_to_format):
    print("Running black...")
    subprocess.run(f"black {files_to_format}", shell=True)
    print("Running isort...")
    subprocess.run(f"isort --profile=black {files_to_format}", shell=True)
    print("Running docformatter")
    if (
        subprocess.run(
            f"docformatter --recursive --in-place --wrap-summaries 88 --wrap-descriptions 88 {files_to_format}",
            shell=True,
        ).rc
        == 3
    ):
        print("Docformatter raised status 3")
    print("Running flake8")
    subprocess.run(
        f"flake8 --ignore=E203,E501,W503 {files_to_format}", shell=True, check=True
    )
