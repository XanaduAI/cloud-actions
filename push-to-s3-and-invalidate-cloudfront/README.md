# Action to push files to an S3 bucket to deploy a static web application

This action can be used to update a static web application that is built using AWS S3 and Cloudfront. The action pushes built code to an S3 bucket that already exists. The intended use case for this action is for Pull Request previews.

Files are pushed to the S3 bucket only when the triggering workflow is a pull request. Moreover the scenarios below describe how each step in the action is mutually exclusive with the other steps.

## When a new Pull Request is created
When a new pull request is created, the action will upload the specified folder (`build-directory`) to a folder named `PR-<number>` on the S3 bucket, where `<number>` is the pull request number and `build-directory` is the folder containing all the built files.

## When an existing Pull Request is updated with new commits
When new commits are pushed to an existing pull request, the action will upload the specified folder (`build-directory`) to the pull request folder that was used in the earlier run. The action also deletes stale files from the folder on S3. 
The action then invalidates the cloudfront cache only for the corresponding `PR-<number>` path.

## When a Pull Request is closed without merging
When a pull request is closed without merging, the action will delete the corresponding `PR-<number>` folder on S3.

## When a Pull Request is merged
When a pull request is merged into a branch that is not the `main` branch then the action does nothing. This may consequently trigger a different scenario if there is already a pull request open for the branch being merged into.

When a pull request is merged into the `main` branch, then the action will delete the corresponding `PR-<number>` folder on S3. The action will then upload the specified folder (`build-directory`) to the root folder of the bucket and invalidate the cloudfront cache for the entire site.

## AWS Permissions
The IAM machine user needs the following permissions on the S3 bucket and the Cloudfront distribution:
```
s3:ListBucket
s3:GetObject
s3:PutObject
s3:DeleteObject
cloudfront:CreateInvalidation
```

## Example Usage
The following example demonstrates a typical use of this action

```yaml
- uses: XanaduAI/cloud-actions/push-to-s3-and-invalidate-cloudfront@main
  with:
    s3-bucket: myBucket
    build-directory: myBuildDir
    pull-request-number: 123
    aws-cloudfront-distribution-id: ${{ secrets.AWS_CLOUDFRONT_DISTRIBUTION_ID }}
    aws-region: ${{ secrets.AWS_REGION }}
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```
