# Pinned Pull Request Comment

This action enabled you to have *pinned* comments on pull requests.

"pinned" in this case means updating an existing comment instead of creating a new 
comment each time from GitHub Actions.


## Creating a pinned comment
```yaml
- uses: XanaduAI/cloud-actions/pinned-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      **Sample pinned comment**
      Thank you for opening this PR.
```

## Updating comments with results
```yaml
- id: results
  uses: my-action/results@v1
 
- uses: XanaduAI/cloud-actions/pinned-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      *Results are*: ${{ steps.results.outputs.result }}
```

## Managing multiple sticky comments
The `pinned_comment_uid` is an arbitrary string that you can use to manage multiple
pinned comments. 

**NOTE:** Updating this parameter will always generate a new comment

```yaml
- id: resultsA
  uses: my-action/results@v1
  with:
    param: A

- id: resultsB
  uses: my-action/results@v1
  with:
    param: B
 
- uses: XanaduAI/cloud-actions/pinned-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pinned_comment_uid: resultA
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      *Results are*: ${{ steps.resultsA.outputs.result }}

- uses: XanaduAI/cloud-actions/pinned-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pinned_comment_uid: resultB
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      *Results are*: ${{ steps.resultsB.outputs.result }}
```
