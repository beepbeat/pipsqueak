"""
board_commands.py - Commands for board manipulation

Copyright (c) 2018 The Fuel Rats Mischief,
All rights reserved.

Licensed under the BSD 3-Clause License.

See LICENSE.md

This module is built on top of the Pydle system.

"""
from Modules.rat_command import *
from Modules.permissions import *
from Modules.rat_rescue import *

log = logging.getLogger(f"{config.Logging.base_logger}.{__name__}")
board = object  # Dummy object
# FIXME: Actually adapt the board object, once it exists.


@require_permission(RAT)
@Commands.command("!go", "!go-.?.?")  # is there RegEx support?
def cmd_go(bot, trigger: Trigger, words, *remainder):
    """
    :param bot:
    :param trigger:
    :type trigger: Trigger
    :param words:
    :param remainder:
    Adds all given Rats to the given case, replies with an (localized, NYI) response
    """
    lang = str(words[0]).replace("!go-", "")
    rescue: Rescue = board.getCase(words[1])
    rats = words[2:]
    # alternative: rats.append(Rat(ratName)) for ratName in words[2:]

    with rescue.change():
        rescue.addRats(rats)

    # response with LocalizedString


def cmd_clear(bot, trigger: Trigger, words, *remainder):
    None

# TODO: add the following commands:
#   !cr
#   !active, !inactive
#   !md
#   !close, !clear
#   !invalid / !other
#   !inject
#   !list / !quote
#   !sys / !cmdr / !nick
#   ...
# TODO: localization / fact support
