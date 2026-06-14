from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sbobot.parser import BuildCommand

logger = structlog.get_logger()


def is_command_authorised(
    *,
    command: "BuildCommand",
    allowed_commentators: list[str],
    allowed_contributors: list[str],
) -> bool:
    if command.mr_id is not None:
        if command.commentator not in allowed_commentators:
            logger.info(
                "Comment was not made by an admin.", commentator=command.commentator
            )

            if command.commentator not in allowed_contributors:
                logger.info(
                    "Comment was not made by a contributor.",
                    commentator=command.commentator,
                )
                return False

            if not command.commentator_is_owner:
                logger.info(
                    "Comment was not on the contributor's own PR.",
                    commentator=command.commentator,
                )
                return False

        return True

    if command.issue_id is not None:
        if command.commentator not in allowed_commentators:
            logger.info(
                "Comment was not made by an admin.", commentator=command.commentator
            )
            return False

        return True

    msg = "Invalid state"
    raise ValueError(msg)
