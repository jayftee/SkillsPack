# utils/

**Generic helpers that know nothing about this project.** This is the folder most likely to turn into
a dumping ground, so its rules are strict. When in doubt, the code does not belong here.

## A function belongs here only if ALL of these are true
1. **It is pure.** The same inputs always give the same output. It reads and writes nothing: no files,
   network, databases, environment variables, clock or random numbers. No module-level state.
2. **It imports nothing from this package.** Only the standard library and third-party packages.
   `poe imports` fails if `utils` imports any other layer.
3. **It uses no word from this project's domain.** If its name, parameters or docstring mention an
   order, a customer, a parcel, a greeting or any other project concept, it belongs to the layer that
   owns that concept.
4. **It would work unchanged in an unrelated project.** Ask yourself: "Could I copy this file into a
   different repository and use it there as-is?"
5. **It has unit tests** in `tests/unit/utils/` that cover its edge cases.

## Where it goes instead
| The helper... | Put it in |
|---|---|
| mentions a domain concept | the layer that owns that concept (usually `services/` or `models/`) |
| reads or writes anything | `repositories/` (your data) or `clients/` (someone else's system) |
| reads settings or environment variables | `config/` |
| is used by a single module | that module, as a private function (`_helper`) |

## File names
Name each file after its topic: `text.py`, `dates.py`, `paths.py`, `iterables.py`.
Never `helpers.py`, `misc.py`, `common.py`, `tools.py` or `utils.py`, because names like that invite
anything.

## Examples
| Belongs here | Does not belong here (and where it goes) |
|---|---|
| `collapse_whitespace(text)` | `normalise_customer_name(name)`: domain word, so `services/` or `models/` |
| `chunked(items, size)` | `load_lines(path)`: reads a file, so `repositories/` |
| `parse_iso_date(text)` | `today_folder()`: reads the clock, so the caller passes the date in |
