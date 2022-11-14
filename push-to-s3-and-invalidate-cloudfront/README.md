# Action to push files to an S3 bucket to deploy a static web application

This action can be used to update a static web application that is built using AWS S3 and Cloudfront. The action pushes built code to an S3 bucket that already exists. One of the intended use cases for this action is Pull Request previews.

Files are pushed to the S3 bucket depending on the user inputs supplied when the action is called. Some inputs have default values or may be inferred from the github context.
Following examples describe how to use the action.

## Uploading to S3 based on user input
This example will **upload** the specified folder (`build-directory`) to a folder named `blog` on the S3 bucket(`myS3Bucket`). The action will not exclude any files while uploading them. The action will also invalidate the cloudfront cache. The action will attempt a max of `5` (based on `aws-retry-attempts` value) retries for any AWS operations before erroring out.

```yaml
- uses: XanaduAI/cloud-actions/push-to-s3-and-invalidate-cloudfront@main
  with:
    build-directory: build-dir
    pull-request-number: 123
    aws-cloudfront-distribution-id: ${{ secrets.AWS_CLOUDFRONT_DISTRIBUTION_ID }}
    aws-region: ${{ secrets.AWS_REGION }}
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    s3-bucket: myS3Bucket
    s3-action: "upload"
    s3-dir-to-upload-to: "blog"
    s3-files-to-exclude: ""
    invalidate-cloudfront-cache: "true"
    aws-retry-attempts: 5
```

## Deleting from S3 based on user input
This example will **delete** the specified folder (`build-directory`) from the S3 bucket(`myS3Bucket`). The action will also invalidate the cloudfront cache.  The action will attempt a max of `5` (based on `aws-retry-attempts` value) retries for any AWS operations before erroring out.


```yaml
- uses: XanaduAI/cloud-actions/push-to-s3-and-invalidate-cloudfront@main
  with:
    build-directory: build-dir
    pull-request-number: 123
    aws-cloudfront-distribution-id: ${{ secrets.AWS_CLOUDFRONT_DISTRIBUTION_ID }}
    aws-region: ${{ secrets.AWS_REGION }}
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    s3-bucket: myS3Bucket
    s3-action: "delete"
    s3-dir-to-delete-from: "blog"
    invalidate-cloudfront-cache: "true"
    aws-retry-attempts: 5
```

## Uploading/Deleting to/from S3 with minimal user unput
If this action is called when a `pull_request` is `opened` or `syncronized`, then the example will **upload** the specified folder (`build-directory`) to a folder named `pr-previews/PR-123` on the S3 bucket (`myS3Bucket`). The action will exclude any files that start with the default `pr-previews` prefix. The action will not invalidate the cloudfront cache.

If this action is called when a `pull_request` is `closed`, then the example will **delete** the folder named `pr-previews/PR-123` on the S3 bucket (`myS3Bucket`).
The action will attempt a max of `2` (default) retries for any AWS operations before erroring out.

```yaml
- uses: XanaduAI/cloud-actions/push-to-s3-and-invalidate-cloudfront@main
  with:
    build-directory: build-dir
    pull-request-number: 123
    aws-cloudfront-distribution-id: ${{ secrets.AWS_CLOUDFRONT_DISTRIBUTION_ID }}
    aws-region: ${{ secrets.AWS_REGION }}
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    s3-bucket: myS3Bucket
```
## AWS Permissions
The IAM machine user needs the following permissions on the S3 bucket and the Cloudfront distribution:
```
s3:ListBucket
s3:GetObject
s3:PutObject
s3:DeleteObject
cloudfront:CreateInvalidation
```
