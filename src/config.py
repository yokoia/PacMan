
import json
import sys
from pathlib import Path


class ConfigError(Exception):
    """Represent an error when loading a configuration file."""


class ConfigLoader:
    DEFAULT_CONFIG = {
        "width": 15,
        "height": 15,
        "seed": 42,
        "lives": 3,
        "level_max_time": 90,
        "points_per_pacgum": 10,
        "points_per_super_pacgum": 50,
        "points_per_ghost": 200,
    }

    # Minimum and maximum accepted values
    CONFIG_LIMITS = {
        "width": (14, 26),
        "height": (14, 26),
        "seed": (0, 2147483647),
        "lives": (1, 99),
        "level_max_time": (10, 3600),
        "points_per_pacgum": (0, 100000),
        "points_per_super_pacgum": (0, 100000),
        "points_per_ghost": (0, 100000),
    }

    def __init__(self, filename: str) -> None:
        self.filename = filename

    @staticmethod
    def remove_comments(content: str) -> str:
        """Remove # comments without modifying JSON strings."""

        clean_lines = []

        for line in content.splitlines():
            in_string = False
            escaped = False
            clean_line = ""

            for char in line:
                if escaped:
                    clean_line += char
                    escaped = False
                    continue

                if char == "\\" and in_string:
                    clean_line += char
                    escaped = True
                    continue

                if char == '"':
                    in_string = not in_string

                if char == "#" and not in_string:
                    break

                clean_line += char

            clean_lines.append(clean_line)

        return "\n".join(clean_lines)

    def validate_config(self, data: dict[str, object]) -> dict[str, int]:
        """Validate configuration values and apply safe defaults."""

        config = self.DEFAULT_CONFIG.copy()

        for key, default_value in self.DEFAULT_CONFIG.items():

            if key not in data:
                print(
                    f"Config warning: Missing '{key}'. "
                    f"Using default: {default_value}",
                    file=sys.stderr,
                )
                continue

            value = data[key]
            minimum, maximum = self.CONFIG_LIMITS[key]

            if type(value) is not int:
                print(
                    f"Config warning: Invalid type for '{key}'. "
                    f"Using default: {default_value}",
                    file=sys.stderr,
                )
                continue

            if not minimum <= value <= maximum:
                print(
                    f"Config warning: '{key}' must be between "
                    f"{minimum} and {maximum}. "
                    f"Using default: {default_value}",
                    file=sys.stderr,
                )
                continue

            config[key] = value

        return config

    def load(self) -> dict[str, int]:
        """Load, parse, and validate a JSON configuration file."""

        path = Path(self.filename)

        try:
            with path.open("r", encoding="utf-8") as file:
                content = file.read()

        except (OSError, UnicodeError) as error:
            raise ConfigError(
                f"Cannot read configuration file '{self.filename}': {error}"
            ) from None

        clean_content = self.remove_comments(content)

        try:
            data = json.loads(
                clean_content,
                object_pairs_hook=self.check_duplicate_keys
            )

        except json.JSONDecodeError as error:
            print(
                f"Config warning: Invalid JSON at line {error.lineno}, "
                f"column {error.colno}: {error.msg}. "
                "Using default configuration.",
                file=sys.stderr,
            )
            return self.DEFAULT_CONFIG.copy()

        except ConfigError as error:
            print(
                f"Config warning: {error} "
                "Using default configuration.",
                file=sys.stderr,
            )
            return self.DEFAULT_CONFIG.copy()

        # JSON root must be an object
        if not isinstance(data, dict):
            print(
                "Config warning: Root must be a JSON object. "
                "Using default configuration.",
                file=sys.stderr,
            )
            return self.DEFAULT_CONFIG.copy()

        return self.validate_config(data)

    @staticmethod
    def check_duplicate_keys(
        pairs: list[tuple[str, object]]
    ) -> dict[str, object]:
        """Reject duplicate keys in JSON objects."""

        data = {}

        for key, value in pairs:
            if key in data:
                raise ConfigError(
                    f"Duplicate key '{key}' in configuration file."
                )

            data[key] = value

        return data
