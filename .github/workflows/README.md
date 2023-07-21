# Re-usable workflows
According to GitHub Actions [documentation](https://docs.github.com/en/actions/using-workflows/reusing-workflows#calling-a-reusable-workflow), workflows can be re-used between repos only if placed under `.github/workflows` folder.

The path to a re-usable workflow from another repo must be:
`{owner}/{repo}/.github/workflows/{filename}@{ref}`
