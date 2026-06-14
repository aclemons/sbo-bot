import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

PR_COMMENT_RE = re.compile(
    "^(?:@|/)sbo-bot:? (rebuild|build|lint) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+)$"
)

ISSUE_COMMENT_RE = re.compile(
    "^(?:@|/)sbo-bot:? (rebuild|build|lint) ((amd64|x86_64|arm|i586) )?([a-zA-z]+\\/[a-zA-Z0-9\\+\\-\\._]+|all)$"
)

if TYPE_CHECKING:
    from typing import Any, Literal, Protocol

    ArchValue = Literal["arm", "i586", "x86_64"]

    class PayloadParserProtocol(Protocol):
        def parse(self, payload: dict[str, Any]) -> "BuildCommand | None": ...


@dataclass
class BuildCommand:
    commentator_is_owner: bool
    commentator: str
    comment_id: int
    project_id: int
    mr_id: int | None
    issue_id: int | None
    arches: "list[ArchValue]"
    target: str
    command: "Literal['lint', 'build', 'rebuild']"
    repo: str


def get_action(action_name: str) -> "Literal['lint', 'build', 'rebuild']":
    if action_name == "lint":
        return "lint"
    if action_name == "rebuild":
        return "rebuild"

    return "build"


def get_arches(parsed_arch: str | None) -> "list[Literal['arm', 'i586', 'x86_64']]":
    build_arch: Literal["arm", "i586", "x86_64"] | None = None

    match parsed_arch:
        case "arm":
            build_arch = "arm"
        case "i586":
            build_arch = "i586"
        case "x86_64" | "amd64":
            build_arch = "x86_64"
        case None:
            build_arch = None
        case _:
            msg = f"Unhandled arch {parsed_arch}"
            raise ValueError(msg)

    return [build_arch] if build_arch else ["i586", "x86_64"]
