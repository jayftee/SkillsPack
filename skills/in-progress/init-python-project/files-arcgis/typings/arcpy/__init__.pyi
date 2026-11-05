# Replaces the type stubs shipped with arcpy, so mypy treats arcpy as untyped (Any).
#
# Why: ArcGIS Pro 3.7.2's arcpy/typing/gp.pyi has a syntax error (an overload, `getOuput`, with no body).
# mypy stops at the first syntax error in any stub it reads, and no mypy setting avoids reading it;
# this file wins because typings/ is on mypy_path, ahead of installed packages.
#
# Remove the typings/arcpy folder once an ArcGIS Pro release fixes gp.pyi, to get arcpy's real types
# back: if `poe types` still passes without it, it is no longer needed.
from typing import Any

def __getattr__(name: str) -> Any: ...
