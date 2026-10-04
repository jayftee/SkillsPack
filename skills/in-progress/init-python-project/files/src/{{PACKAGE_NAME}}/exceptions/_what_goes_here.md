# exceptions/

**Errors this package raises on purpose.**

## Belongs here
- `errors.py`, with one base class (`ApplicationError`) and specific subclasses (`ConfigurationError`,
  `RecordNotFoundError`).
- Split it into more files only when `errors.py` becomes hard to read.

## Rules
- Every error the package raises on purpose derives from `ApplicationError`, so a caller can catch
  everything this package deliberately rejects in one place.
- Wrap third-party errors where they enter the project (`raise RecordNotFoundError(...) from error`)
  so they don't leak up through the services.
- No logic here: an exception class holds a message and, at most, a few fields describing the failure.

## May import
`utils` and the standard library only (`poe imports` enforces this).
