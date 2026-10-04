# config/

**Loading and validating settings:** environment variables, configuration files, defaults.

## Belongs here
- A frozen `Settings` data class for each area, plus a `load_...()` function that reads the values,
  applies defaults and validates them.
- Converting raw text into typed values (`int`, `Path`, enums), failing early with a `ConfigurationError`.

## Does not belong here
- Using the settings: other layers receive a `Settings` object (or individual values) as arguments.
- Reading `os.environ` anywhere else. Pass the mapping in, as the sample does, so tests can use a
  plain dict.

## May import
`models`, `enums`, `exceptions`, `utils`. Never `services`, `repositories` or `clients` (`poe imports` enforces this).
