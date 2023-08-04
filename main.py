from pathpicker import parse, state_files
from pathpicker.formatted_text import FormattedText
from pathpicker.line_format import LineBase, LineMatch, SimpleLine
from pathpicker.screen_flags import ScreenFlags
from pathpicker.usage_strings import USAGE_STR

from pathpicker.line_format import LineBase, LineMatch, SimpleLine
from process_input import get_line_objs_from_lines
from subprocess import check_output, STDOUT

import logging
import sys
from os import system

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    filename="/tmp/_tmux_fpp.log",
    filemode="a",
)

logger = logging.getLogger(__name__)


class TmuxFppException(Exception):
    pass


class NotFoundException(TmuxFppException):
    """Did not find any match!"""


def select(filepath):
    system("tmux send -X other-end")
    system("tmux send -X search-backward '{}'".format(filepath))
    system("tmux send -X begin-selection")
    system("tmux send -X -N {} cursor-right".format(len(filepath) - 1))
    system("tmux send -X stop-selection")


def capture_buffer_lines():
    tmux_capture_cmd = "tmux capture-pane -pS -999999999"

    tmux_buffer = check_output(tmux_capture_cmd, stderr=STDOUT, shell=True).decode()
    tmux_buffer_lines = tmux_buffer.splitlines()

    logger.info("Total captured lines = %d", len(tmux_buffer_lines))

    return tmux_buffer_lines


def parse_last_filepath(lines, target_index):
    found = 0
    for line in reversed(lines):
        line = line.replace("\t", " " * 4)
        # remove the new line as we place the cursor ourselves for each
        # line. this avoids curses errors when we newline past the end of the
        # screen
        line = line.replace("\n", "")
        formatted_line = FormattedText(line)
        result = parse.match_line(
            str(formatted_line),
            validate_file_exists=True,
            all_input=False,
        )
        logger.info(f"{line=} || {result=}")
        if result:
            if found == target_index:
                logger.info(f"Matched, {target_index=}, {result=}")
                return result
            else:
                logger.info(f"Found {found=} match, {result=}")
                found += 1

    # TODO if find any, display the last match
    raise NotFoundException("Didn't find any match!!!")


def get_index():
    with open("/tmp/.tmux_fpp.txt", "r") as f:
        index = int(f.read())

    return index


def main():
    logger.info("------start new match--------")
    lines = capture_buffer_lines()
    index = get_index()
    logger.info(f"To get {index=}")
    system("tmux copy-mode")
    try:
        last_file_path_match = parse_last_filepath(lines, index)
    except NotFoundException as e:
        print(str(e))
        sys.exit(1)

    last_file_path_str = last_file_path_match[0]
    select(last_file_path_str)


try:
    main()
except:
    logger.exception("error")
