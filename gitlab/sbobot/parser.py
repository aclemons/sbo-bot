import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol

MR_COMMENT_RE = re.compile(
    "^(?:@|/)sbo-bot:? (rebuild|build|lint) ((x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+)$"
)

ISSUE_COMMENT_RE = re.compile(
    "^(?:@|/)sbo-bot:? (rebuild|build|lint) ((x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+|all)$"
)

ArchValue = Literal["arm", "i586", "x86_64"]


@dataclass
class BuildCommand:
    commentator_is_owner: bool
    commentator: str
    comment_id: int
    project_id: int
    mr_id: int | None
    issue_id: int | None
    arches: list[ArchValue]
    target: str
    command: Literal["lint", "build", "rebuild"]
    repo: str


if TYPE_CHECKING:

    class PayloadParserProtocol(Protocol):
        def parse(self, payload: dict[str, Any]) -> BuildCommand | None: ...


class PayloadParser:
    def parse(self, payload: dict[str, Any]) -> BuildCommand | None:
        if payload["object_kind"] != "note":
            return None

        if (
            payload["object_attributes"]["noteable_type"] != "MergeRequest"
            and payload["object_attributes"]["noteable_type"] != "Issue"
        ):
            return None

        commentator = payload["user"]["username"]
        comment_id = payload["object_attributes"]["id"]
        comment: str = payload["object_attributes"]["note"]

        mr_id = None
        issue_id = None
        if payload["object_attributes"]["noteable_type"] == "MergeRequest":
            mr_id = payload["merge_request"]["iid"]
            commentator_is_owner = (
                payload["merge_request"]["author_id"] == payload["user"]["id"]
            )

            match = MR_COMMENT_RE.match(comment)
        elif payload["object_attributes"]["noteable_type"] == "Issue":
            issue_id = payload["issue"]["iid"]
            commentator_is_owner = (
                payload["issue"]["author_id"] == payload["user"]["id"]
            )

            match = ISSUE_COMMENT_RE.match(comment)
        else:
            msg = "Invalid state"
            raise ValueError(msg)

        project_id = payload["project_id"]

        if not match:
            return None

        if match[1] == "lint":
            action = "lint"
        elif match[1] == "rebuild":
            action = "rebuild"
        else:
            action = "build"

        parsed_arch = match[3]

        build_arch: ArchValue | None = None
        match parsed_arch:
            case "arm":
                build_arch = "arm"
            case "i586":
                build_arch = "i586"
            case "x86_64":
                build_arch = "x86_64"
            case None:
                build_arch = None
            case _:
                msg = f"Unhandled arch {parsed_arch}"
                raise ValueError(msg)

        build_package = match[4]

        return BuildCommand(
            commentator_is_owner=commentator_is_owner,
            commentator=commentator,
            comment_id=comment_id,
            mr_id=mr_id,
            issue_id=issue_id,
            project_id=project_id,
            arches=[build_arch] if build_arch else ["i586", "x86_64"],
            target=build_package,
            command=action,
            repo=payload["project"]["path_with_namespace"],
        )
