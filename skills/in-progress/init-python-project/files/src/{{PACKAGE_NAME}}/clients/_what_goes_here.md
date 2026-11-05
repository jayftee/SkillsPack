# clients/

**Calls to systems outside this process that this project does not own:** web APIs, remote services,
external tools.

## Belongs here
- One class per external system (`WeatherClient`), hiding its protocol, authentication and error format.
- Conversion between the external format and this project's `models`.
- Turning the external system's failures into this project's `exceptions`.

## Does not belong here
| If it... | Put it in |
|---|---|
| stores or reads this project's own data | `repositories/` |
| decides what to do with the response | `services/` |
| holds URLs, keys or timeouts | `config/`; the client receives them as arguments |

## May import
`config`, `models`, `enums`, `exceptions`, `utils`. Never `services` or `repositories` (`poe imports` enforces this).

## Tests
Unit tests replace the network with fakes. Tests that call the real system go in `tests/integration/`
and carry `@pytest.mark.external`.
