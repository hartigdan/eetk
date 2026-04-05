from collections.abc import Iterable
from copy import copy
from io import DEFAULT_BUFFER_SIZE

from .commands import Command, Position, Span


class PeekableTextReader:
    _chunk_size = DEFAULT_BUFFER_SIZE

    def __init__(self, stream):
        self._stream = stream
        self._buffer = ""
        self._pos = 0

    def _fill(self, n: int):
        """Stellt sicher, dass mindestens n Zeichen verfügbar sind."""
        while len(self._buffer) - self._pos < n:
            chunk = self._stream.read(self._chunk_size)
            if not chunk:
                break
            self._buffer += chunk

    def _compact(self):
        """Bereinigt bereits konsumierten Buffer."""
        if self._pos > 0:
            self._buffer = self._buffer[self._pos :]
            self._pos = 0

    def peek(self, n: int = 1) -> str:
        self._fill(n)
        return self._buffer[self._pos : self._pos + n]

    def read(self, n: int = -1) -> str:
        if n == -1:
            result = self._buffer[self._pos :]
            self._buffer = ""
            self._pos = 0
            return result + self._stream.read()

        self._fill(n)
        end = self._pos + n
        result = self._buffer[self._pos : end]
        self._pos = min(end, len(self._buffer))

        if self._pos > self._chunk_size:
            self._compact()

        return result


def parse(input):
    with open(input) as f:
        # f muss io.TextIOWrapper sein damit newline normalisiert wird
        pipeline = PeekableTextReader(f)
        pipeline = _read_commands(pipeline)
        # pipeline = _parse_commands(pipeline)
        yield from pipeline


def _read_commands(input: PeekableTextReader):
    from enum import Enum

    class State(Enum):
        TOP = 1
        EXT = 2
        EXT_WORD = 3
        WORD = 4

    state = State.TOP
    cursor = Position(1, 1)
    command_text = []
    command_start = copy(cursor)

    word_offset = 0
    word_length = 0
    words = []

    def _read_char(capture=True):
        nonlocal input, command_text, cursor
        c = input.read(1)
        if capture:
            command_text.append(c)
        cursor.column += 1

    def _handle_whitespace(next, capture=True):
        nonlocal cursor
        if next == "\n":
            _read_char(capture)
            cursor.line += 1
            return True
        elif next.isspace():
            _read_char(capture)
            return True
        else:
            return False

    def _skip_empty_word(next):
        nonlocal input, cursor
        if next == "*":
            input.read(1)
            cursor.column += 1
            return True
        else:
            return False

    def _commit_word():
        nonlocal word_length, words, word_offset
        _read_char()
        word_length += 1
        words.append(slice(word_offset, word_offset + word_length - 1))
        word_offset = word_offset + word_length

    def _make_command():
        nonlocal command_text, words, command_start, cursor
        command = Command(
            text="".join(command_text),
            words=words,
            source=Span(start=command_start, end=copy(cursor)),
        )
        command_text = []
        words = []
        return command

    while next := input.peek(1):
        match state:
            case State.TOP:
                if _handle_whitespace(next, False) or _skip_empty_word(next):
                    continue
                elif next == "%":
                    # start of extended command
                    command_start = copy(cursor)
                    _read_char()
                    word_offset = 1
                    word_length = 0
                    state = State.EXT
                else:
                    # start of word command
                    command_start = copy(cursor)
                    _read_char()
                    word_offset = 0
                    word_length = 1
                    state = State.WORD
            case State.EXT:
                if _handle_whitespace(next) or _skip_empty_word(next):
                    word_offset += 1
                elif next == "%":
                    # end of extended command
                    _read_char()
                    yield _make_command()
                    state = State.TOP
                else:
                    # start of word in extended command
                    _read_char()
                    word_length = 1
                    state = State.EXT_WORD
            case State.EXT_WORD | State.WORD:
                if _handle_whitespace(next):
                    word_length += 1
                elif next == "*":
                    # end of word
                    _commit_word()
                    if state == State.EXT_WORD:
                        # came from extended command
                        state = State.EXT
                    else:
                        # came from word command
                        yield _make_command()
                        state = State.TOP
                else:
                    # still within word
                    _read_char()
                    word_length += 1


# def _parse_commands(input):
#    for command, line in input:
#        f3, f2, f1, l3 = command[0:3], command[0:2], command[0:1], command[-4:-1]
#        # fmt: off
#        if   l3 == "D01"        : yield _parse_D01    (command, line)
#        elif l3 == "D02"        : yield _parse_D02    (command, line)
#        elif l3 == "D03"        : yield _parse_D03    (command, line)
#        elif f3 == "G01"        : yield _parse_G01    (command, line)
#        elif f3 == "G02"        : yield _parse_G02    (command, line)
#        elif f3 == "G03"        : yield _parse_G03    (command, line)
#        elif f3 == "G04"        : yield _parse_G04    (command, line)
#        elif f3 == "G36"        : yield _parse_G36    (command, line)
#        elif f3 == "G37"        : yield _parse_G37    (command, line)
#        elif f3 == "G54"        : yield _parse_G54    (command, line)
#        elif f3 == "G70"        : yield _parse_G70    (command, line)
#        elif f3 == "G71"        : yield _parse_G71    (command, line)
#        elif f3 == "G74"        : yield _parse_G74    (command, line)
#        elif f3 == "G75"        : yield _parse_G75    (command, line)
#        elif f3 == "G90"        : yield _parse_G90    (command, line)
#        elif f3 == "G91"        : yield _parse_G91    (command, line)
#        elif f3 == "M00"        : yield _parse_M00    (command, line)
#        elif f3 == "M01"        : yield _parse_M01    (command, line)
#        elif f3 == "M02"        : yield _parse_M02    (command, line)
#        elif f2 == "AD"         : yield _parse_AD     (command, line)
#        elif f2 == "AS"         : yield _parse_AS     (command, line)
#        elif f2 == "LP"         : yield _parse_LP     (command, line)
#        elif f2 == "TO"         : yield _parse_TO     (command, line)
#        elif f2 == "TD"         : yield _parse_TD     (command, line)
#        elif f2 == "TA"         : yield _parse_TA     (command, line)
#        elif f2 == "TF"         : yield _parse_TF     (command, line)
#        elif f2 == "AM"         : yield _parse_AM     (command, line)
#        elif f2 == "FS"         : yield _parse_FS     (command, line)
#        elif f2 == "MI"         : yield _parse_MI     (command, line)
#        elif f2 == "MO"         : yield _parse_MO     (command, line)
#        elif f2 == "OF"         : yield _parse_OF     (command, line)
#        elif f2 == "IP"         : yield _parse_IP     (command, line)
#        elif f2 == "LN"         : yield _parse_LN     (command, line)
#        elif f2 == "IN"         : yield _parse_IN     (command, line)
#        elif f2 == "SF"         : yield _parse_SF     (command, line)
#        elif f2 == "SR"         : yield _parse_SR     (command, line)
#        elif f1 == "D"          : yield _parse_D      (command, line)
#        elif f1 in "XYIJ"       : yield _parse_Coord  (command, line)
#        elif command == "*"     : yield _parse_Ignore (command, line)
#        elif command == "ICAS*" : yield _parse_Ignore (command, line)
#        else:
#            raise ParserError("unknown command", command, line)
#        # fmt: on


# elif last_op:
#    try:
#        cmd = cmd.removesuffix("*")
#        _parse_coords(command) # may fail
#        # TODO: Deprecation Warning
#        cmd = f"{cmd}{last_op}*"
#        if   last_op == "D01": yield _parse_D01(command)
#        elif last_op == "D02": yield _parse_D02(command)
#        elif last_op == "D03": yield _parse_D03(command)
#    except Exception as e:
#        raise GerberError() from e

# def _parse_XYIJ(s: str) -> dict[str, int]:
#    c = {}
#    n = len(s)
#    i = 0
#
#    if n == 0:
#        raise Exception("Zero length")
#
#    while i < n:
#        # first char must be X, Y, I or J identifying the axis
#        a = s[i]
#        if a in c:
#            raise Exception("Duplicate axis")
#        elif a not in "XYIJ":
#            raise Exception("Unknown axis")
#        i += 1
#
#        # next must be the value
#        v = ""
#        while i < n and s[i] in "-0123456789":
#            v += s[i]
#            i += 1
#
#        try:
#            c[a] = int(v)
#        except ValueError:
#            raise Exception("Invalid value")
#
#    return c
