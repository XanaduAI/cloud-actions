# Manage GitHub Deployment
[GitHub Deployments](https://docs.github.com/en/rest/deployments/deployments) are a method to deploy and track the
deployment of a specific Git Reference. 

This actions allows the calling workflow to create/update/delete deployments.

## Sample usages
### Minimal 
**Workflow Triggered on Pull Request**
```yaml
- uses: XanaduAI/cloud-actions/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: in_progress
    deployment_ref: ${{ github.event.pull_request.head.ref }}

- run: |
    for i in {1..5}
    do
      echo "Deploy in progress ($i/5)..."
    done
    echo "Deploy success!"

- uses: XanaduAI/cloud-actions/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: success
    deployment_ref: ${{ github.event.pull_request.head.ref }}
```

**Workflow Triggered on Push to branch**
Use the same example as above but replace `${{ github.event.pull_request.head.ref }}` with `${{ github.ref_name }}`.


### Updating the same deployment
By default, each time this action is called, it will delete the existing deployment, then create a new deployment with 
the deployment_stage passed. 

This behavior can be changed by passing the `deployment_id` output of the action between steps. This makes the action
update the deployment status in place instead of creating a new deployment each time.

```yaml
- uses: XanaduAI/cloud-actions/manage-gh-deployments@main
  id: deployment
  with:
    environment: pull_request_preview
    deployment_stage: in_progress
    deployment_ref: ${{ github.event.pull_request.head.ref }}

- run: |
    for i in {1..5}
    do
      echo "Deploy in progress ($i/5)..."
    done
    echo "Deploy success!"

- uses: XanaduAI/cloud-actions/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: success
    deployment_ref: ${{ github.event.pull_request.head.ref }}
    deployment_id: ${{ steps.deployment.outputs.deployment_id }}
```

### Deleting a deployment
The deletion of a deployment is marked by the `inactive` status. 

```yaml
- run: |
    for i in {1..5}
    do
      echo "Teardown in progress ($i/5)..."
    done
    echo "Teardown success!"

- uses: XanaduAI/cloud-actions/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: inactive
    deployment_ref: ${{ github.event.pull_request.head.ref }}
```


## Inputs
### `environment` [required]

The current deployment environment, ex: `production`, `staging`, `development`. The value can be any string; for example
if you want a deployment per pull request you can have a `pull_request_preview` environment.

### `deployment_stage` [required]
The current status of the deployment, once the deployment has been created, the status passed here will be attached to it.

Valid values are:
- `pending`    -> The app has not been picked up for deployment yet
- `queued`     -> The app is queued for deployment, the deployment process should start soon
- `in_progress`-> The app is currently being deployed. For most cases this might be the first status you create for a deployment
- `error`      -> There is an error in the app. It cannot be deployed
- `failure`    -> There was an error while deploying the error
- `success`    -> The app was successfully deployed
- `inactive`   -> The deployment has been torndown and can be removed from GitHub

### `deployment_ref` [required]
This is the current git branch that is being deployed.

If the workflow is running on.pull_request, you can access this value by using: `${{ github.event.pull_request.head.ref }}`

If the workflow is running on.push, you can access this value by using: `${{ github.ref_name }}`

### `deployment_id` [optional, default='']
By default, each time this action is called, it deletes all the deployments for a branch within the environment and
re-creates a new deployment with the status passed. This behavior is fine for most cases but if the deployment id
is relevant, then this can be passed between the different steps and the deployment status will be updated in-place
without being re-created. See example above on how to utilise this input.

### `deployment_description` [optional, default='']
The deployment description to attach at creation time (not used if an existing deployment is being updated in-place).

### `deployment_log_url` [optional, default='']
The current action url in most cases. A link to the deployment logs for the current deployment.

Sample way of crafting this value:
```yaml
deployment_log_url: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

### `deployment_url` [optional, default='']
This is the link to the app. On GitHub users can see a 'View Deployment' button and clicking it would take them to the 
URL specified for this input.

### `required_contexts` [optional, default='']
By default, when creating a deployment, GitHub requires that there are no failed checks against the current ref.
However, at time you may want to only ensure a subset of workflows passing before creating a deployment, or disable
the check altogether. This input enables the user to toggle that behavior.

Sample:
```yaml
- uses: XanaduAI/cloud-actions/manage-gh-deployments@main
  id: deployment
  with:
    environment: pull_request_preview
    deployment_stage: in_progress
    deployment_ref: ${{ github.event.pull_request.head.ref }}
    required_contexts: |
      unittest (linux)
      another_workflow
```
The input can take multiline string OR comma separated values (`a,b,c`)

To disable the check altogether, set this input to `null`

## Outputs
### `deployment_id`
The ID of the deployment that was created or updated.
