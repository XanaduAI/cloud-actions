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
