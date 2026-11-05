# models/

**Domain objects:** the nouns of this project, written as data classes, typed dicts or small value types.

## Belongs here
- `@dataclass(frozen=True)` classes describing the things the project works with (an order, a parcel, a greeting).
- Small behaviour that only reads the object's own fields (a computed property, a check on itself).
- Data transfer objects passed between layers.

## Does not belong here
| If it... | Put it in |
|---|---|
| reads or writes files, databases or the network | `repositories/` or `clients/` |
| coordinates several objects or applies business rules | `services/` |
| is an enumeration on its own | `enums/` |
| parses settings | `config/` |

## May import
`enums`, `exceptions`, `utils`, the standard library and third-party packages. Never `config`,
`repositories`, `clients` or `services` (`poe imports` enforces this).

## One file per concept
`order.py` holds `Order` (and any small type that only `Order` uses). Avoid a single `models.py` that
keeps growing.
