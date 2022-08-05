# Create and Update Pull Request Comment

This actions allows the calling function to create a comment on a pull request from within GitHub Actions; and then update
that comment on subsequent workflow runs instead of creating a new comment each time.

If a new comment has to be created each time, that is allowed by this action as well.


## Creating a comment
```yaml
- uses: XanaduAI/cloud-actions/create-and-update-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      **Sample comment**
      Thank you for opening this PR.
```

## Updating comments with results
```yaml
- id: results
  uses: my-action/results@v1

- uses: XanaduAI/cloud-actions/create-and-update-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      *Results are*: ${{ steps.results.outputs.result }}
```

## Managing multiple comments
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

- uses: XanaduAI/cloud-actions/create-and-update-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     comment_uid: resultA
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      *Results for A are*: ${{ steps.resultsA.outputs.result }}

- uses: XanaduAI/cloud-actions/create-and-update-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     comment_uid: resultB
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_body: |
      *Results for B are*: ${{ steps.resultsB.outputs.result }}
```

## Create new comment every time
```yaml
- uses: XanaduAI/cloud-actions/create-and-update-pull-request-comment@main
  with:
     github_token: ${{ github.token }}
     pull_request_number: ${{ github.event.pull_request.number }}
     comment_uid: ''
     comment_body: |
      **Sample comment**
      Thank you for opening this PR.
```
