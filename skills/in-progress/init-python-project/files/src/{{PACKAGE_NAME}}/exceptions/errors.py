"""Errors raised by this package."""


class ApplicationError(Exception):
    """Base class for every error this package raises on purpose."""


class ConfigurationError(ApplicationError):
    """Settings are missing or invalid."""
