# repositories/

**Reading and writing data this project stores or owns:** files, databases, geodatabases, caches.

## Belongs here
- One class per kind of stored data (`OrderRepository`) that accepts and returns `models`.
- SQL, file formats, paths and connection handling: everything about *how* the data is stored.

## Does not belong here
| If it... | Put it in |
|---|---|
| calls a system someone else owns (web API, remote service) | `clients/` |
| decides what to do with the data | `services/` |
| reads connection strings or paths from settings | `config/`; the repository receives them as arguments |

## May import
`config`, `models`, `enums`, `exceptions`, `utils`. Never `services` or `clients` (`poe imports` enforces this).

## Tests
Unit-test the mapping logic with fakes or temporary files. Tests that need a real database go in
`tests/integration/` and carry `@pytest.mark.database`.
