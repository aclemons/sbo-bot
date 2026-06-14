from typing import TYPE_CHECKING

from sbobot.parser import (
    ISSUE_COMMENT_RE,
    PR_COMMENT_RE,
    BuildCommand,
    get_action,
    get_arches,
)

if TYPE_CHECKING:
    import re
    from typing import Any


class PayloadParser:
    def parse(self, payload: "dict[str, Any]") -> "BuildCommand | None":
        comment_data = payload.get("comment")
        sender_data = payload.get("sender")
        repository_data = payload.get("repository")

        if comment_data is None or sender_data is None or repository_data is None:
            return None

        issue_data = payload.get("issue")
        pull_request_data = payload.get("pull_request")

        if issue_data is not None:
            return self._parse_issue_comment(
                issue_data=issue_data,
                comment_data=comment_data,
                sender_data=sender_data,
                repository_data=repository_data,
            )

        if pull_request_data is not None:
            return self._parse_pull_request_comment(
                pull_request_data=pull_request_data,
                comment_data=comment_data,
                sender_data=sender_data,
                repository_data=repository_data,
            )

        return None

    def _parse_issue_comment(
        self,
        *,
        issue_data: "dict[str, Any]",
        comment_data: "dict[str, Any]",
        sender_data: "dict[str, Any]",
        repository_data: "dict[str, Any]",
    ) -> "BuildCommand | None":
        is_pull_request = issue_data.get("pull_request") is not None

        match = self._match_comment(
            comment=comment_data["body"],
            is_pull_request=is_pull_request,
        )

        if match is None:
            return None

        commentator_is_owner = issue_data["user"]["id"] == sender_data["id"]
        action = get_action(match[1])
        arches = get_arches(match[3])
        target = match[4]

        return BuildCommand(
            commentator_is_owner=commentator_is_owner,
            commentator=sender_data["login"],
            comment_id=comment_data["id"],
            mr_id=issue_data["number"] if is_pull_request else None,
            issue_id=None if is_pull_request else issue_data["number"],
            project_id=repository_data["id"],
            arches=arches,
            target=target,
            command=action,
            repo=repository_data["full_name"],
        )

    def _parse_pull_request_comment(
        self,
        *,
        pull_request_data: "dict[str, Any]",
        comment_data: "dict[str, Any]",
        sender_data: "dict[str, Any]",
        repository_data: "dict[str, Any]",
    ) -> "BuildCommand | None":
        match = self._match_comment(comment=comment_data["body"], is_pull_request=True)

        if match is None:
            return None

        commentator_is_owner = pull_request_data["user"]["id"] == sender_data["id"]
        action = get_action(match[1])
        arches = get_arches(match[3])
        target = match[4]

        return BuildCommand(
            commentator_is_owner=commentator_is_owner,
            commentator=sender_data["login"],
            comment_id=comment_data["id"],
            mr_id=pull_request_data["number"],
            issue_id=None,
            project_id=repository_data["id"],
            arches=arches,
            target=target,
            command=action,
            repo=repository_data["full_name"],
        )

    def _match_comment(
        self, *, comment: str, is_pull_request: bool
    ) -> "re.Match[str] | None":
        if is_pull_request:
            return PR_COMMENT_RE.match(comment)

        return ISSUE_COMMENT_RE.match(comment)
