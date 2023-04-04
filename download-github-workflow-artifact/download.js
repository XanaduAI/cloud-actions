let fs = require('fs');

module.exports = async ({github, context}, workflow_run_id, artifact_name_regex, artifact_download_dir, max_retry) => {
    // Exponential backoff with a ceiling at 30 seconds
    const backoffDelay = (retryCount) => new Promise(resolve => setTimeout(resolve, 100 * Math.min(300, 1 << retryCount)));

    const downloadArtifact = async (artifact) => {
        let download = await github.rest.actions.downloadArtifact({
            owner: context.repo.owner,
            repo: context.repo.repo,
            artifact_id: artifact.id,
            archive_format: 'zip'
        });
        fs.writeFileSync(`${artifact_download_dir}/${artifact.name}.zip`, Buffer.from(download.data));
    };

    let artifactsAllOpts = github.rest.actions.listWorkflowRunArtifacts.endpoint.merge({
        owner: context.repo.owner,
        repo: context.repo.repo,
        run_id: workflow_run_id
    });
    let artifactsAll = await github.paginate(artifactsAllOpts);
    let artifactsFiltered = artifactsAll.data.artifacts.filter((artifact) => {
        return artifact.name.match(artifact_name_regex)
    });

    /*
      Attempt to download the artifact one at a time and save them to disk.
      In the event of an error, back-off (incrementally) and try again.

      Each error increases the back-off delay by 1s, in other words:
      > failure -> wait (1s) -> try-again -> failure -> wait (2s) -> try-again -> ...

      This deals with network congestion and rate-limiting errors that occur if the artifact
      download happens during a time of high load on GitHub Actions.
    */
    for (const artifact of artifactsFiltered) {
        for (let i = 1; i < max_retry + 1; i++) {
            const artifactFullName = `${artifact_download_dir}/${artifact.name}.zip`;
            try {
                console.log(`Attempting to download artifact (${artifact.id}): ${artifactFullName}`);
                await downloadArtifact(artifact);
                console.log(`Successfully downloaded artifact (${artifact.id}): ${artifactFullName}`);
                break;
            } catch (e) {
                console.log(`Error while trying to download artifact (${artifact.id}): ${artifactFullName}, retryCount: ${i}, error: ${e}`);
                ['message', 'status', 'request', 'response'].forEach((attr) => {
                    if (e.hasOwnProperty(attr)) {
                        console.log(`error_${attr}:`);
                        console.log(e[attr]);
                    }
                });
                if (i === max_retry) throw new Error(e);
                console.log(`Retrying download of artifact (${artifact.id}): ${artifactFullName}`);
                await backoffDelay(i);
            }
        }
    }
}
