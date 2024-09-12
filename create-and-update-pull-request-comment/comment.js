module.exports = async ({github, context}, prNumber, commentUid, commentBody) => {
    // Static User ID of the GitHub Actions Bot
    // Sample Reference: https://github.com/orgs/community/discussions/26560
    const actionsBotUserId = 41898282;

    const commentHeader = `<!-- ${commentUid} -->`;
    const commentContent = `${commentBody}\n${commentHeader}`;
    console.log(commentContent);

    if (commentUid) {
      const opts = github.rest.issues.listComments.endpoint.merge({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: prNumber
      });
      const comments = await github.paginate(opts);

      // Find any comment already made by the bot.
      const botComment = comments.find(comment => comment.user.id === actionsBotUserId && comment.body.trim().endsWith(commentHeader));

      if (botComment) {
        await github.rest.issues.updateComment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            comment_id: botComment.id,
            body: commentContent
        });

        return;
      }
    }

    await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        body: commentContent
    });
}
