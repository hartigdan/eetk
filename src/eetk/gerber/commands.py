from dataclasses import dataclass

# Ignore = namedtuple("Ignore", "s")
# Coord = namedtuple("Coord", "s")


@dataclass(slots=True)
class Position:
    line: int
    column: int


@dataclass(slots=True)
class Span:
    start: Position
    end: Position


@dataclass(slots=True)
class Command:
    text: str
    source: Span
    words: list[slice]


class ParserError(Exception):
    def __init__(self, message, command, line):
        super().__init__(f'{message}: "{command}" at line {line}')


@dataclass(slots=True)
class AD(Command):
    pass


@dataclass(slots=True)
class AM(Command):
    pass


@dataclass(slots=True)
class AS(Command):
    pass


@dataclass(slots=True)
class Dnn(Command):
    pass


@dataclass(slots=True)
class D01(Command):
    pass


@dataclass(slots=True)
class D02(Command):
    pass


@dataclass(slots=True)
class D03(Command):
    pass


@dataclass(slots=True)
class FS(Command):
    pass


@dataclass(slots=True)
class G01(Command):
    pass


@dataclass(slots=True)
class G02(Command):
    pass


@dataclass(slots=True)
class G03(Command):
    pass


@dataclass(slots=True)
class G04(Command):
    pass


@dataclass(slots=True)
class G36(Command):
    pass


@dataclass(slots=True)
class G37(Command):
    pass


@dataclass(slots=True)
class G54(Command):
    pass


@dataclass(slots=True)
class G70(Command):
    pass


@dataclass(slots=True)
class G71(Command):
    pass


@dataclass(slots=True)
class G74(Command):
    pass


@dataclass(slots=True)
class G75(Command):
    pass


@dataclass(slots=True)
class G90(Command):
    pass


@dataclass(slots=True)
class G91(Command):
    pass


@dataclass(slots=True)
class IN(Command):
    pass


@dataclass(slots=True)
class IP(Command):
    pass


@dataclass(slots=True)
class IP(Command):
    pass


@dataclass(slots=True)
class LN(Command):
    pass


@dataclass(slots=True)
class LP(Command):
    pass


@dataclass(slots=True)
class M00(Command):
    pass


@dataclass(slots=True)
class M02(Command):
    pass


@dataclass(slots=True)
class MI(Command):
    pass


@dataclass(slots=True)
class MO(Command):
    pass


@dataclass(slots=True)
class OF(Command):
    pass


@dataclass(slots=True)
class SF(Command):
    pass


@dataclass(slots=True)
class SR(Command):
    pass


@dataclass(slots=True)
class TA(Command):
    pass


@dataclass(slots=True)
class TD(Command):
    pass


@dataclass(slots=True)
class TF(Command):
    pass


@dataclass(slots=True)
class TO(Command):
    pass
