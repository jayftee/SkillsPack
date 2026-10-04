# enums/

**Enumerations:** fixed sets of named values used by more than one layer.

## Belongs here
- `StrEnum`, `IntEnum` or `Enum` classes, one concept per file (`greeting_style.py`).
- Prefer `StrEnum` when the value is read from or written to text (settings, JSON, a database column).

## Does not belong here
- Constants that are not a closed set of choices: keep them in the module that uses them.
- Logic beyond a trivial helper on the enum itself: that belongs in `services/`.

## May import
`exceptions`, `utils` and the standard library. Nothing from the layers above (`poe imports` enforces this).
