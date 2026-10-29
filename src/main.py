"""Dependency graph visualizer. Stage 1: Configuration."""
import argparse
import os
import sys
import yaml

MIN_DEPTH = 1
VALID_MODES = ("real", "test")


class ConfigError(Exception):
    """Exception raised for configuration errors."""


def load_yaml(path: str) -> dict:
    """Load YAML configuration from a file."""
    if not os.path.isfile(path):
        raise ConfigError(f"Config file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML format: {exc}")

    if not isinstance(config, dict):
        raise ConfigError("Config root must be a mapping (dictionary).")
    return config


def validate_str(config: dict, key: str) -> str:
    """Validate that a key exists and is a non-empty string."""
    val = config.get(key)
    if val is None:
        raise ConfigError(f"Missing required parameter: '{key}'")
    if not isinstance(val, str) or not val.strip():
        raise ConfigError(f"Parameter '{key}' must be a non-empty string.")
    return val


def validate_int(config: dict, key: str, min_val: int) -> int:
    """Validate that a key exists and is an integer >= min_val."""
    val = config.get(key)
    if val is None:
        raise ConfigError(f"Missing required parameter: '{key}'")
    if not isinstance(val, int):
        raise ConfigError(f"Parameter '{key}' must be an integer.")
    if val < min_val:
        raise ConfigError(f"Parameter '{key}' must be >= {min_val}.")
    return val


def validate_config(config: dict) -> dict:
    """Validate all parameters and return a clean dictionary."""
    validated = {}
    validated["package_name"] = validate_str(config, "package_name")
    validated["repo_url"] = validate_str(config, "repo_url")
    
    mode = validate_str(config, "repo_mode")
    if mode not in VALID_MODES:
        raise ConfigError(
            f"Parameter 'repo_mode' must be one of {VALID_MODES}."
        )
    validated["repo_mode"] = mode
    
    validated["package_version"] = validate_str(
        config, "package_version"
    )
    validated["output_filename"] = validate_str(
        config, "output_filename"
    )
    validated["max_depth"] = validate_int(
        config, "max_depth", MIN_DEPTH
    )
    
    return validated


def print_parameters(params: dict) -> None:
    """Print parameters in key-value format."""
    print("=== Configuration Parameters ===")
    for key, value in params.items():
        print(f"{key}: {value}")
    print("=================================")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer. Stage 1."
    )
    parser.add_argument(
        "-c", "--config", required=True,
        help="Path to YAML configuration file"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    try:
        raw_config = load_yaml(args.config)
        valid_config = validate_config(raw_config)
        print_parameters(valid_config)
    except ConfigError as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()