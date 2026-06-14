from typing import TYPE_CHECKING

from sbobot.parser import ISSUE_COMMENT_RE, BuildCommand, get_action, get_arches
from sbobot.parser import PR_COMMENT_RE as MR_COMMENT_RE

if TYPE_CHECKING:
    import re
    from typing import Any


class PayloadParser:
    def parse(self, payload: "dict[str, Any]") -> "BuildCommand | None":
        if payload["object_kind"] != "note":
            return None

        if (
            payload["object_attributes"]["noteable_type"] != "MergeRequest"
            and payload["object_attributes"]["noteable_type"] != "Issue"
        ):
            return None

        noteable_type = payload["object_attributes"]["noteable_type"]

        if noteable_type == "MergeRequest":
            return self._parse_merge_request(payload)

        if noteable_type == "Issue":
            return self._parse_issue(payload)

        msg = "Invalid state"
        raise ValueError(msg)

    def _parse_merge_request(self, payload: "dict[str, Any]") -> "BuildCommand | None":
        comment: str = payload["object_attributes"]["note"]
        match = MR_COMMENT_RE.match(comment)

        if not match:
            return None

        commentator_is_owner = (
            payload["merge_request"]["author_id"] == payload["user"]["id"]
        )

        return self._build_command(
            payload=payload,
            match=match,
            commentator_is_owner=commentator_is_owner,
            mr_id=payload["merge_request"]["iid"],
            issue_id=None,
        )

    def _parse_issue(self, payload: "dict[str, Any]") -> "BuildCommand | None":
        comment: str = payload["object_attributes"]["note"]
        match = ISSUE_COMMENT_RE.match(comment)

        if not match:
            return None

        commentator_is_owner = payload["issue"]["author_id"] == payload["user"]["id"]

        return self._build_command(
            payload=payload,
            match=match,
            commentator_is_owner=commentator_is_owner,
            mr_id=None,
            issue_id=payload["issue"]["iid"],
        )

    def _build_command(
        self,
        *,
        payload: "dict[str, Any]",
        match: "re.Match[str]",
        commentator_is_owner: bool,
        mr_id: int | None,
        issue_id: int | None,
    ) -> BuildCommand:
        action = get_action(match[1])
        arches = get_arches(match[3])
        build_package = match[4]

        return BuildCommand(
            commentator_is_owner=commentator_is_owner,
            commentator=payload["user"]["username"],
            comment_id=payload["object_attributes"]["id"],
            mr_id=mr_id,
            issue_id=issue_id,
            project_id=payload["project_id"],
            arches=arches,
            target=build_package,
            command=action,
            repo=payload["project"]["path_with_namespace"],
        )
