from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve
from zipfile import ZipFile
from itertools import chain

import pytest

import eetk.gerber as gerber


def pytest_generate_tests(metafunc):
    if "gerbv_example" in metafunc.fixturenames:
        examples = _get_gerbv_examples()
        metafunc.parametrize("gerbv_example", examples, ids=[e.name for e in examples])


@pytest.fixture(scope="session")
def gerbv_examples():
    return _get_gerbv_examples()


@lru_cache
def _get_gerbv_examples():
    """
    Download gerbv example files.

    Gerbv is licensed under GPLv2, which is not compatible with the MIT license. In
    order to still be able to use the sample files, we must ensure that they do not
    become part of our distribution.
    """
    url = "https://github.com/gerbv/gerbv/archive/refs/tags/v2.12.0.zip"
    chksum = "59d27afe07ec65b6400882a918b0f8c7c993a7aa81e9ebc3f5b5a0920dd8e512"
    dir = Path(__file__).parent / "gerbv_examples"
    zipfile = dir / f"{chksum}.zip"

    dir.mkdir(exist_ok=True)
    dir.joinpath(".gitignore").write_text("*")

    if not zipfile.exists():
        urlretrieve(url, zipfile)
        assert sha256(zipfile.read_bytes()).hexdigest() == chksum
        with TemporaryDirectory() as td:
            td = Path(td)
            with ZipFile(zipfile) as zf:
                zf.extractall(td)
            copytree(
                next(td.glob("gerbv*")).joinpath("example"), dir, dirs_exist_ok=True
            )

    includes = [
        ".apr",
        ".asb",
        ".ast",
        ".bot",
        ".drd",
        ".exc",
        ".gbl",
        ".gbo",
        ".gbp",
        ".gbr",
        ".gbs",
        ".gbx",
        ".gd1",
        ".gdo",
        ".ger",
        ".gg1",
        ".gm1",
        ".gm2",
        ".gp1",
        ".grb",
        ".gtl",
        ".gto",
        ".gtp",
        ".gts",
        ".off",
        ".rul",
        ".smb",
        ".smt",
        ".ssb",
        ".sst",
        ".top",
    ]

    excludes = [".pcb.output_plated-drill.grb", ".pcb.output_unplated-drill.grb"]

    files = [f for f in dir.glob("**/*")]
    files = [f for f in files if f.is_file()]
    files = [f for f in files if any(str(f).lower().endswith(i) for i in includes)]
    files = [f for f in files if not any(str(f).lower().endswith(e) for e in excludes)]

    return files


def test_gerbv_example(gerbv_example):
    print(gerbv_example)
    try:
        for _ in gerber.parse(gerbv_example):
            pass
    except Exception as e:
        raise Exception(f"Failed to parse {gerbv_example}") from e
