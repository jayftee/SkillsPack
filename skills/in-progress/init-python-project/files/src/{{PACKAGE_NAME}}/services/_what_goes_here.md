# services/

**Business logic and orchestration:** what the project actually *does*.

## Belongs here
- Classes or functions that apply the project's rules: calculate, decide, transform, coordinate.
- Workflows that call repositories and clients to fetch data and to send results out.

## Does not belong here
| If it... | Put it in |
|---|---|
| talks to a file, database or API directly | `repositories/` or `clients/`; the service calls it |
| parses command-line arguments or environment variables | `config/` (argument wiring stays in `__main__.py`) |
| is a plain data shape | `models/` |
| would make sense in an unrelated project | `utils/`, after checking its rules |

## May import
Every other layer. Services are the top layer: nothing in the package imports a service except
`__main__.py`.

## Keep it testable
Take collaborators (a repository, a client) as constructor or function arguments, so unit tests can
pass in fakes.
