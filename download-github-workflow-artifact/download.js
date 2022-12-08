let fs = require('fs');

module.exports = async ({github, context}, workflow_run_id, artifact_name_regex, artifact_download_dir, max_retry = 15) => {
    const backoffDelay = (retryCount) => new Promise(resolve => setTimeout(resolve, 1000 * retryCount));

    const downloadArtifact = async (artifact) => {
        let download = await github.rest.actions.downloadArtifact({
            owner: context.repo.owner,
            repo: context.repo.repo,
            artifact_id: artifact.id,
            archive_format: 'zip'
        });
        fs.writeFileSync(`${artifact_download_dir}/${artifact.name}`, Buffer.from(download.data));
    };

    let artifactsAll = await github.rest.actions.listWorkflowRunArtifacts({
        owner: context.repo.owner,
        repo: context.repo.repo,
        run_id: workflow_run_id
    });
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
            try {
                console.log(`Attempting to download artifact: ${artifact.name}`);
                await downloadArtifact(artifact);
                console.log(`Successfully downloaded artifact: ${artifact.name}`);
                break;
            } catch (e) {
                console.log(`Error while trying to download artifact: ${artifact.name}, i: ${i}, error: ${e}`);
                ['message', 'status', 'request', 'response'].forEach((attr) => {
                    if (e.hasOwnProperty(attr)) {
                        console.log(`error_${attr}:`);
                        console.log(e[attr]);
                    }
                });
                if (i === max_retry) throw new Error(e);
                console.log(`Retrying download of artifact: ${artifact.name}`);
                await backoffDelay(i);
            }
        }
    }
}
