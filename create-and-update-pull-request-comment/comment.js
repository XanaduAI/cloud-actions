module.exports = async ({github, context}, prNumber, repositoryOwner, repositoryName, commentUid, commentBody) => {
    // Static User ID of the GitHub Actions Bot
    // Sample Reference: https://github.com/orgs/community/discussions/26560
    const actionsBotUserId = 41898282;

    const [ repository_owner, repository_name ] = (repositoryName && repositoryName.includes('/')) ? repositoryName.split('/', 2) : [
      repositoryOwner || context.repo.owner,
      repositoryName || context.repo.repo
    ];

    const commentHeader = `<!-- ${commentUid} -->`;
    const commentContent = `${commentBody}\n${commentHeader}`;
    console.log(commentContent);

    if (commentUid) {
      const opts = github.rest.issues.listComments.endpoint.merge({
          owner: repository_owner,
          repo: repository_name,
          issue_number: prNumber
      });
      const comments = await github.paginate(opts);

      // Find any comment already made by the bot.
      const botComment = comments.find(comment => comment.user.id === actionsBotUserId && comment.body.trim().endsWith(commentHeader));

      if (botComment) {
        await github.rest.issues.updateComment({
            owner: repository_owner,
            repo: repository_name,
            comment_id: botComment.id,
            body: commentContent
        });

        return;
      }
    }

    await github.rest.issues.createComment({
        owner: repository_owner,
        repo: repository_name,
        issue_number: prNumber,
        body: commentContent
    });
}
