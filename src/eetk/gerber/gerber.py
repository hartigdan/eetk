import re
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from itertools import accumulate
from typing import ClassVar, NoReturn


class Source:
    def __init__(self, text, line_bounds):
        self._text = text
        self._line_bounds = line_bounds

    @classmethod
    def from_file(cls, file):
        with open(file) as f:
            lines = f.readlines()
        return cls(
            text="".join(lines),
            line_bounds=[0, *accumulate(map(len, lines))],
        )

    def view(self):
        return SourceView(self, 0, len(self._text))


# TODO: Cursor extrahieren
class SourceView:
    __slots__ = ("_source", "_start", "_stop", "_position")

    def __init__(self, source, start, stop):
        self._source = source
        self._start = start
        self._stop = stop
        self._position = start

    def startswith(self, s):
        return self._source._text.startswith(s, self._start, self._stop)

    def endswith(self, s):
        return self._source._text.endswith(s, self._start, self._stop)

    def match_by(self, re):
        return re.match(self._source._text, self._start, self._stop)

    def peek(self):
        if self._position >= self._stop:
            return None
        return self._source._text[self._position]

    def advance(self):
        if self._position < self._stop:
            self._position += 1

    def tell(self):
        return self._position

    def __str__(self):
        return self._source._text[self._start : self._stop]

    def __len__(self):
        return self._stop - self._start

    def __getitem__(self, subscript):
        if isinstance(subscript, int):
            subscript = slice(subscript, subscript + 1)
        elif isinstance(subscript, slice):
            pass
        else:
            raise TypeError("subscript must be int or slice")

        start, stop, step = subscript.indices(len(self))
        if step != 1:
            raise IndexError("step is not supported")

        return type(self)(self._source, self._start + start, self._start + stop)


class GerberError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Feature(Enum):
    UNKNOWN = auto()
    LOW_RESOLUTION = auto()
    INCREMENTAL_NOTATION = auto()
    TRAILING_ZERO_OMISSION = auto()


class FeatureAction(Enum):
    ALLOW = auto()
    WARN = auto()
    DENY = auto()


@dataclass
class FeaturePolicy:
    action: FeatureAction = FeatureAction.ALLOW
    rationale: str = "default"


class FeatureGate:
    def __init__(self, policies: dict[Feature, FeaturePolicy], diagnostics):


    def hit(self, feature: Feature):
        pass


# deprecation ist eigentlich orthogonal zur policy
# ein feature kann
# - allowed aber deprecated sein -> warning
# - allowed und nicht deprecated sein -> nix tun
# - denied und deprected/nicht deprecated sein -> error
#
# Policy:
# - Allow
# - Warn
# - Deny
#
#
#

# @dataclass(frozen=True)
# class Features:
#    low_resolution_is_deprecated: bool = False
#    incremental_notation_is_deprecated: bool = False
#    trailing_zero_omission_is_deprecated: bool = False
#
#    @classmethod
#    def for_revision(cls, revision: int):
#        revision = 202405 if not revision
#        return cls(
#            low_resolution_is_deprecated=revision >= 201506,
#            incremental_notation_is_deprecated=revision >= 201212,
#            trailing_zero_omission_is_deprecated=revision >= 201506,
#        )


class Severity(IntEnum):
    INFO = 1
    WARNING = 2
    ERROR = 3

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Diag:
    severity: Severity
    message: str
    source: SourceView | None

    def __str__(self):
        s = f"[{self.severity}]: {self.message}"
        return s


class Diagnostics:
    def __init__(self, abort_level=Severity.ERROR):
        self._diags = []
        if not isinstance(abort_level, Severity):
            raise TypeError("abort_level must be of type Severity")
        self._abort_level = abort_level

    def _add(self, severity, message, source):
        self._diags.append(Diag(severity, message, source))
        if severity >= self._abort_level:
            raise GerberError(message)

    def info(self, message, source=None):
        self._add(Severity.INFO, message, source)  # may return

    def warn(self, message, source=None):
        self._add(Severity.WARNING, message, source)  # may return

    def err(self, message, source=None) -> NoReturn:
        self._add(Severity.ERROR, message, source)  # definitely doesn't return
        assert False, "unreachable"


@dataclass(frozen=True)
class RawCommand:
    command: SourceView
    words: list[SourceView]


class Lexer:
    def __init__(self, source, diag):
        self._source = source
        self._diag = diag

    def __iter__(self):
        TOP, EXT, EXT_WORD, WORD = range(4)

        state = TOP
        command_start = 0
        word_start = 0
        words = []
        source = self._source.view()

        while (ch := source.peek()) is not None:
            if state == TOP:
                if ch.isspace():
                    source.advance()
                elif ch == "*":
                    self._diag.info("skipped empty word command")
                    source.advance()
                elif ch == "%":
                    # start of extended command
                    command_start = source.tell()
                    source.advance()
                    state = EXT
                else:
                    # start of word command
                    word_start = command_start = source.tell()
                    source.advance()
                    state = WORD
            elif state == EXT:
                if ch.isspace():
                    source.advance()
                elif ch == "*":
                    self._diag.info("skipped empty word")
                    source.advance()
                elif ch == "%":
                    # end of extended command
                    source.advance()
                    if words:
                        yield RawCommand(
                            command=source[command_start : source.tell()],
                            words=words.copy(),
                        )
                        words.clear()
                    else:
                        self._diag.info("skipped empty extended command")
                    state = TOP
                else:
                    # start of word in extended command
                    word_start = source.tell()
                    source.advance()
                    state = EXT_WORD
            elif state in (WORD, EXT_WORD):
                if ch.isspace():
                    source.advance()
                elif ch == "*":
                    # end of word
                    words.append(source[word_start : source.tell()])
                    source.advance()
                    word_start = source.tell()
                    if state == EXT_WORD:
                        # came from extended command
                        state = EXT
                    else:
                        yield RawCommand(
                            command=source[command_start : source.tell()],
                            words=words.copy(),
                        )
                        words.clear()
                        state = TOP
                else:
                    # still within word
                    source.advance()


class Parser:
    def __init__(self, lexer, diag):
        self._lexer = lexer
        self._diag = diag

    def __iter__(self):
        xyij = ("X", "Y", "I", "J")
        for raw_command in self._lexer:
            w = raw_command.words[0]
            # fmt: off
            if   w.endswith("D01"):   yield not_impl_yet("D01")
            elif w.endswith("D02"):   yield not_impl_yet("D02")
            elif w.endswith("D03"):   yield not_impl_yet("D03")
            elif w.startswith(xyij):  yield not_impl_yet("XYIJ")
            elif w.startswith("G36"): yield not_impl_yet("G36")
            elif w.startswith("G37"): yield not_impl_yet("G37")
            elif w.startswith("AD"):  yield not_impl_yet("AD")
            elif w.startswith("G01"): yield not_impl_yet("G01")
            elif w.startswith("G03"): yield not_impl_yet("G03")
            elif w.startswith("D"):   yield not_impl_yet("D")
            elif w.startswith("G54"): yield not_impl_yet("G54")
            elif w.startswith("G04"): yield G04.parse(raw_command, self._diag)
            elif w.startswith("G02"): yield not_impl_yet("G02")
            elif w.startswith("G70"): yield not_impl_yet("G70")
            elif w.startswith("G71"): yield not_impl_yet("G71")
            elif w.startswith("G74"): yield not_impl_yet("G74")
            elif w.startswith("G75"): yield not_impl_yet("G75")
            elif w.startswith("G90"): yield not_impl_yet("G90")
            elif w.startswith("G91"): yield not_impl_yet("G91")
            elif w.startswith("M00"): yield not_impl_yet("M00")
            elif w.startswith("M01"): yield not_impl_yet("M01")
            elif w.startswith("M02"): yield not_impl_yet("M02")
            elif w.startswith("AS"):  yield not_impl_yet("AS")
            elif w.startswith("LP"):  yield not_impl_yet("LP")
            elif w.startswith("TO"):  yield not_impl_yet("TO")
            elif w.startswith("TD"):  yield not_impl_yet("TD")
            elif w.startswith("TA"):  yield not_impl_yet("TA")
            elif w.startswith("TF"):  yield not_impl_yet("TF")
            elif w.startswith("AM"):  yield not_impl_yet("AM")
            elif w.startswith("FS"):  yield FS.parse(raw_command, self._diag)
            elif w.startswith("MI"):  yield not_impl_yet("MI")
            elif w.startswith("MO"):  yield not_impl_yet("MO")
            elif w.startswith("OF"):  yield not_impl_yet("OF")
            elif w.startswith("IP"):  yield not_impl_yet("IP")
            elif w.startswith("LN"):  yield not_impl_yet("LN")
            elif w.startswith("IN"):  yield not_impl_yet("IN")
            elif w.startswith("SF"):  yield not_impl_yet("SF")
            elif w.startswith("SR"):  yield not_impl_yet("SR")
            else:
                self._diag.err("unknown command")
            # fmt: on


def read(f):
    source = Source.from_file(f)
    diag = Diagnostics()
    lexer = Lexer(source, diag)
    parser = Parser(lexer, diag)
    for command in parser:
        if command:
            print(command)
        # pass

    for d in diag._diags:
        print(d)

    # t = timeit(fn, number=1)
    # print(json.dumps({"STATS": {"t": t}}))


def not_impl_yet(cmd):
    return None


def expect_word(raw_command, diag):
    if len(raw_command.words) != 1:
        diag.err(f"expected 1 word, got {len(raw_command.words)}")
    return raw_command.words[0]


@dataclass(frozen=True, slots=True)
class Command:
    pass


@dataclass(frozen=True, slots=True)
class D01(Command):
    x: str
    y: str
    i: str
    j: str


# normal: G04 text
# leer: G04*
# standard: G04 #@! ...
# was ist das denn?: G04:AMPARAMS
# nur utf-8
# alles andere muss escaped werden
@dataclass(frozen=True, slots=True)
class G04(Command):
    text: str

    RE: ClassVar[re.Pattern] = re.compile(
        r"""
        G04
        """
    )

    @classmethod
    def parse(cls, raw_command, diag):
        return f"{raw_command.words[0]}"


@dataclass(frozen=True, slots=True)
class FS(Command):
    integers: int  # num. integer digits 1..6
    decimals: int  # num. decimal digits 1..6
    omission: str  # L = leading zero omission, T = trailing zero omission
    notation: str  # I = incremental, A = absolute

    RE: ClassVar[re.Pattern] = re.compile(
        r"""
        FS (T|L)? (A|I)? (N[\d])?
        X (\d) (\d)
        Y (\d) (\d)
        """,
        re.VERBOSE,
    )

    @classmethod
    def parse(cls, raw_command, diag):
        if not (m := expect_word(raw_command, diag).match_by(cls.RE)):
            diag.err("invalid format specification")

        omission, notation, unknown, *digits = m.groups()
        x_int, x_dec, y_int, y_dec = map(int, digits)

        if unknown:
            diag.warn(f"ignoring unknown extension '{unknown}'")

        if not omission:
            diag.warn("no zero omission rule given, assuming leading zero omission")
            omission = "L"
        elif omission == "T":
            diag.warn("trailing zero omission is deprecated since revision 2015.06")

        if not notation:
            diag.warn("no notation rule given, assuming absolute notation")
            notation = "A"
        elif notation == "I":
            diag.warn("incremental notation is deprecated since revision I1 Dec. 2012")

        if (x_int, x_dec) != (y_int, y_dec):
            diag.err("digits for X and Y must be the same")

        if not (1 <= x_int <= 6 and 1 <= x_dec <= 6):
            diag.err("digits must range from 1 to 6")

        if x_dec < 6:
            diag.warn("using less than 6 decimals is deprecated since revision 2015.06")

        return cls(x_int, x_dec, omission, notation)
