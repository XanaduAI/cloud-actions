# Download GitHub Workflow Artifact

This action allows the calling action to download workflow artifacts from other workflow. It should be noted that if you
are attempting to download artifacts between different jobs within the same workflow, use [actions/download-artifact](https://github.com/actions/download-artifact).


## Sample Usage
#### Workflow being triggered by `workflow_run`
There is a likely scenario where GitHub Actions workflowA runs successfully, creates some artifacts and then finishes
as successful. The completion of that workflow now starts workflowB as workflowB has [on.workflow_run](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
event trigger setup.

This workflowB however, needs access to the artifacts created by workflowA. This can be achieved as shown:
```yaml
- uses: XanaduAI/cloud-actions/download-github-workflow-artifact@main
  with:
    workflow_run_id: ${{ github.event.workflow_run.id }}
    github_token: ${{ github.token }}
```
This will download the artifacts from the original workflow into the current workflows github workspace.

**Download only certain artifacts**
You can pass a regex to match names of artifacts you want to download using the `artifact_name_regex` input.

Using the above example again:
```yaml
- uses: XanaduAI/cloud-actions/download-github-workflow-artifact@main
  with:
    workflow_run_id: ${{ github.event.workflow_run.id }}
    artifact_name_regex: ^html\-.*$
    github_token: ${{ github.token }}
```
This will download only the artifacts that begin with `html-`.

#### Downloading workflows from a different workflow (can be same or separate repo)
Let's say your workflow is not triggered by another workflow, but needs to download artifacts from another run
of a workflow. The most difficult part of this is getting the workflow id. However, that is attainable using GitHub's
rest api `listWorkflowRuns`.

The following code snippet get the most recent successful build of a workflow, then returns the workflow id
```yaml
- name: Get Workflow run ID
  id: workflow_run_id
  uses: actions/github-script@v6
  with:
    result-encoding: string
    script: |
      const workflowRuns = await github.paginate(github.rest.actions.listWorkflowRuns.endpoint.merge({
        owner: context.repo.owner,
        repo: context.repo.repo,
        workflow_id: 'workflow_you_want.yml',
        branch: 'branch-that-workflow-ran-on',
        event: 'event-that-triggered-that-workflow ("push", "pull_request", "schedule")',
        status: 'success'
      }));
      const workflowRunsSorted = workflowRuns.sort((a, b) => b.run_number - a.run_number);

      return workflowRunsSorted[0].id
```
And now you can use the output of this step to call this action. If the artifact is from another repository,
the `owner` and `repo` parameters must be set to point to the repository from which
to download the artifact:
```yaml
- uses: XanaduAI/cloud-actions/download-github-workflow-artifact@main
  with:
    owner: context.repo.owner
    repo: context.repo.repo
    workflow_run_id: ${{ steps.workflow_run_id.outputs.result }}
    github_token: ${{ github.token }}
```
