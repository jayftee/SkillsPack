"""Command-line entry point: ``python -m {{PACKAGE_NAME}}`` or the ``{{PROJECT_NAME}}`` command."""

import os
import sys

from {{PACKAGE_NAME}}.config.settings import load_settings
from {{PACKAGE_NAME}}.exceptions.errors import ConfigurationError
from {{PACKAGE_NAME}}.services.greeting_service import GreetingService

CONFIGURATION_ERROR_EXIT_CODE = 2


def main() -> int:
    """Print a greeting configured by environment variables.

    Returns:
        The process exit code.
    """
    try:
        settings = load_settings(os.environ)
    except ConfigurationError as error:
        print(error, file=sys.stderr)
        return CONFIGURATION_ERROR_EXIT_CODE
    service = GreetingService()
    print(service.render(service.create(settings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
