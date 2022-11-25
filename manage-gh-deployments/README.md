# Manage GitHub Deployment
[GitHub Deployments](https://docs.github.com/en/rest/deployments/deployments) are a method to deploy and track the
deployment of a specific Git Reference. 

This actions allows the calling workflow to create/update/delete deployments.

## Sample usages
### Minimal 
**Workflow Triggered on Pull Request**
```yaml
- uses: XanaduAI/cloud-action/manage-gh-deployments@main
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

- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: success
    deployment_ref: ${{ github.event.pull_request.head.ref }}
```

**Workflow Triggered on Push to branch**
Use the same example as above but replace `${{ github.event.pull_request.head.ref }}` with `${{ github.ref_name }}`.

### Managing multiple deployments within the same deployments from within the same workflow
If the app being deployed has multiple portions that are separate, they can be managed by using different deployment names.

The `deployment_name` parameter is not something that GitHub natively supports, but it is a feature offered by this action
by leveraging the `task` parameter provided by GitHub.

```yaml
- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_name: myApp_${{ github.event.pull_request.head.ref }}_frontend
    deployment_stage: in_progress
    deployment_ref: ${{ github.event.pull_request.head.ref }}

- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_name: myApp_${{ github.event.pull_request.head.ref }}_backend
    deployment_stage: in_progress
    deployment_ref: ${{ github.event.pull_request.head.ref }}

- run: |
    for i in {1..5}
    do
      echo "Deploy frontend progress ($i/5)..."
    done
    echo "Frontend deploy success!"

- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_name: myApp_${{ github.event.pull_request.head.ref }}_frontend
    deployment_stage: success
    deployment_ref: ${{ github.event.pull_request.head.ref }}

- run: |
    for i in {1..5}
    do
      echo "Deploy backend progress ($i/5)..."
    done
    echo "Backend deploy success!"

- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_name: myApp_${{ github.event.pull_request.head.ref }}_backend
    deployment_stage: success
    deployment_ref: ${{ github.event.pull_request.head.ref }}
```

### Updating the same deployment
By default, each time this action is called, it will delete the existing deployment, then create a new deployment with 
the deployment_stage passed. 

This behavior can be changed by passing the `deployment_id` output of the action between steps. This makes the action
update the deployment status in place instead of creating a new deployment each time.

```yaml
- uses: XanaduAI/cloud-action/manage-gh-deployments@main
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

- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: success
    deployment_ref: ${{ github.event.pull_request.head.ref }}
    deployment_id: ${{ steps.deployment.outputs.deployment_id }}
```

### Deleting a deployment
The deletion of a deployment is marked by the `inactive` status. 

```yaml
- uses: XanaduAI/cloud-action/manage-gh-deployments@main
  with:
    environment: pull_request_preview
    deployment_stage: inactive
    deployment_ref: ${{ github.event.pull_request.head.ref }}
```
