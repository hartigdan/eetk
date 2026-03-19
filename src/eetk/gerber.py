from collections import namedtuple

AD = namedtuple("AD", "s")
AM = namedtuple("AM", "s")
AS = namedtuple("AS", "s")
Coord = namedtuple("Coord", "s")
D = namedtuple("D", "s")
D01 = namedtuple("D01", "s")
D02 = namedtuple("D02", "s")
D03 = namedtuple("D03", "s")
FS = namedtuple("FS", "s")
G01 = namedtuple("G01", "s")
G02 = namedtuple("G02", "s")
G03 = namedtuple("G03", "s")
G04 = namedtuple("G04", "s")
G36 = namedtuple("G36", "s")
G37 = namedtuple("G37", "s")
G54 = namedtuple("G54", "s")
G70 = namedtuple("G70", "s")
G71 = namedtuple("G71", "s")
G74 = namedtuple("G74", "s")
G75 = namedtuple("G75", "s")
G90 = namedtuple("G90", "s")
G91 = namedtuple("G91", "s")
IN = namedtuple("IN", "s")
IP = namedtuple("IP", "s")
IP = namedtuple("IP", "s")
LN = namedtuple("LN", "s")
LP = namedtuple("LP", "s")
M00 = namedtuple("M00", "s")
M02 = namedtuple("M02", "s")
MI = namedtuple("MI", "s")
MO = namedtuple("MO", "s")
OF = namedtuple("OF", "s")
SF = namedtuple("SF", "s")
SR = namedtuple("SR", "s")
TA = namedtuple("TA", "s")
TD = namedtuple("TD", "s")
TF = namedtuple("TF", "s")
TO = namedtuple("TO", "s")

Ignore = namedtuple("Ignore", "s")


class ParserError(Exception):
    pass


def parse(input):
    with open(input) as f:
        pipeline = f
        pipeline = _read_commands(pipeline)
        pipeline = _parse_commands(pipeline)
        yield from pipeline


def _parse_commands(input):
    for cmd in input:
        f3, f2, f1, l3 = cmd[0:3], cmd[0:2], cmd[0:1], cmd[-4:-1]
        # fmt: off
        if   l3 == "D01"               : yield _parse_D01    (cmd)
        elif l3 == "D02"               : yield _parse_D02    (cmd)
        elif l3 == "D03"               : yield _parse_D03    (cmd)
        elif f3 == "G01"               : yield _parse_G01    (cmd)
        elif f3 == "G02"               : yield _parse_G02    (cmd)
        elif f3 == "G03"               : yield _parse_G03    (cmd)
        elif f3 == "G04"               : yield _parse_G04    (cmd)
        elif f3 == "G36"               : yield _parse_G36    (cmd)
        elif f3 == "G37"               : yield _parse_G37    (cmd)
        elif f3 == "G54"               : yield _parse_G54    (cmd)
        elif f3 == "G70"               : yield _parse_G70    (cmd)
        elif f3 == "G71"               : yield _parse_G71    (cmd)
        elif f3 == "G74"               : yield _parse_G74    (cmd)
        elif f3 == "G75"               : yield _parse_G75    (cmd)
        elif f3 == "G90"               : yield _parse_G90    (cmd)
        elif f3 == "G91"               : yield _parse_G91    (cmd)
        elif f3 == "M00"               : yield _parse_M00    (cmd)
        elif f3 == "M02"               : yield _parse_M02    (cmd)
        elif f2 == "AD"                : yield _parse_AD     (cmd)
        elif f2 == "AS"                : yield _parse_AS     (cmd)
        elif f2 == "LP"                : yield _parse_LP     (cmd)
        elif f2 == "TO"                : yield _parse_TO     (cmd)
        elif f2 == "TD"                : yield _parse_TD     (cmd)
        elif f2 == "TA"                : yield _parse_TA     (cmd)
        elif f2 == "TF"                : yield _parse_TF     (cmd)
        elif f2 == "AM"                : yield _parse_AM     (cmd)
        elif f2 == "FS"                : yield _parse_FS     (cmd)
        elif f2 == "MI"                : yield _parse_MI     (cmd)
        elif f2 == "MO"                : yield _parse_MO     (cmd)
        elif f2 == "OF"                : yield _parse_OF     (cmd)
        elif f2 == "IP"                : yield _parse_IP     (cmd)
        elif f2 == "LN"                : yield _parse_LN     (cmd)
        elif f2 == "IN"                : yield _parse_IN     (cmd)
        elif f2 == "SF"                : yield _parse_SF     (cmd)
        elif f2 == "SR"                : yield _parse_SR     (cmd)
        elif f1 == "D"                 : yield _parse_D      (cmd)
        elif f1 == "X"                 : yield _parse_Coord  (cmd)
        elif f1 == "Y"                 : yield _parse_Coord  (cmd)
        elif cmd == "*"                : yield _parse_Ignore (cmd)
        elif cmd == "ICAS*"            : yield _parse_Ignore (cmd)
        else:
            raise ParserError(f'Failed to parse command "{cmd}": "{cmd.encode("utf-8").hex()}"')
        # fmt: on


def _read_commands(input):
    while True:
        char = input.read(1)
        if not char:
            # end of input stream
            break
        elif char.isspace() or not char.isprintable():
            # ignore space etc. between commands
            continue
        elif char == "*":
            # empty command
            yield "*"
        elif char == "%":
            # extended command
            yield _read_until(input, "%")[:-1].rstrip()
        else:
            # word command
            yield char + _read_until(input, "*")


def _read_until(input, delimiter):
    buffer = ""
    while True:
        char = input.read(1)
        buffer += char
        if not char or char == delimiter:
            return buffer


def _parse_SR(cmd: str):
    return SR(cmd)


def _parse_SF(cmd: str):
    return SF(cmd)


def _parse_Coord(input: str):
    return Coord(input)


def _parse_G71(cmd: str):
    return G71(cmd)


def _parse_M00(cmd: str):
    return M00(cmd)


def _parse_G02(cmd: str):
    return G02(cmd)


def _parse_MI(cmd: str):
    return MI(cmd)


def _parse_AS(cmd: str):
    return AS(cmd)


def _parse_G90(cmd: str):
    return G90(cmd)


def _parse_G91(cmd: str):
    return G91(cmd)


def _parse_G74(cmd: str):
    return G74(cmd)


def _parse_Ignore(cmd: str):
    return Ignore(cmd)


def _parse_D01(input: str):
    return D01(input)


def _parse_D02(input: str):
    return D02(input)


def _parse_D03(input: str):
    return D03(input)


def _parse_G01(input: str):
    return G01(input)


def _parse_G04(input: str):
    return G04(input)


def _parse_M02(input: str):
    return M02(input)


def _parse_G36(input: str):
    return G36(input)


def _parse_G37(input: str):
    return G37(input)


def _parse_G75(input: str):
    return G75(input)


def _parse_G03(input: str):
    return G03(input)


def _parse_AD(input: str):
    return AD(input)


def _parse_LP(input: str):
    return LP(input)


def _parse_TO(input: str):
    return TO(input)


def _parse_TD(input: str):
    return TD(input)


def _parse_TA(input: str):
    return TA(input)


def _parse_TF(input: str):
    return TF(input)


def _parse_AM(input: str):
    return AM(input)


def _parse_FS(input: str):
    return FS(input)


def _parse_MO(input: str):
    return MO(input)


def _parse_D(input: str):
    return D(input)


def _parse_G70(input: str):
    return G70(input)


def _parse_OF(input: str):
    return OF(input)


def _parse_IP(input: str):
    return IP(input)


def _parse_LN(input: str):
    return LN(input)


def _parse_IN(input: str):
    return IN(input)


def _parse_G54(input: str):
    return G54(input)


# elif last_op:
#    try:
#        cmd = cmd.removesuffix("*")
#        _parse_coords(cmd) # may fail
#        # TODO: Deprecation Warning
#        cmd = f"{cmd}{last_op}*"
#        if   last_op == "D01": yield _parse_D01(cmd)
#        elif last_op == "D02": yield _parse_D02(cmd)
#        elif last_op == "D03": yield _parse_D03(cmd)
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
