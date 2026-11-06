"""Dependency graph visualizer. Stage 2: Fetch apt data."""
import argparse
import gzip
import os
import sys
import urllib.request
import yaml

MIN_DEPTH = 1
VALID_MODES = ("real", "test")


class ConfigError(Exception):
    """Exception raised for configuration or data errors."""


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
        raise ConfigError("Config root must be a mapping.")
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


def fetch_repo_data(url: str) -> str:
    """Download and decompress the Packages file from the URL."""
    try:
        with urllib.request.urlopen(url) as response:
            raw_data = response.read()
    except Exception as exc:
        raise ConfigError(f"Failed to fetch data from {url}: {exc}")

    if url.endswith(".gz"):
        try:
            raw_data = gzip.decompress(raw_data)
        except Exception as exc:
            raise ConfigError(f"Failed to decompress data: {exc}")

    return raw_data.decode("utf-8", errors="ignore")


def parse_packages_file(content: str) -> list:
    """Parse Debian Packages file into a list of dictionaries."""
    packages = []
    current_pkg = {}
    
    for line in content.splitlines():
        if not line.strip():
            if current_pkg:
                packages.append(current_pkg)
                current_pkg = {}
            continue
        
        if ":" in line:
            key, val = line.split(":", 1)
            current_pkg[key.strip()] = val.strip()
            
    if current_pkg:
        packages.append(current_pkg)
        
    return packages


def parse_depends_string(depends: str) -> list:
    """Extract package names from a Depends string."""
    dependencies = []
    for dep in depends.split(","):
        dep = dep.strip()
        if not dep:
            continue
        # Берем первую альтернативу (до |)
        first_alt = dep.split("|")[0].strip()
        # Убираем версию (>= 1.0)
        if "(" in first_alt:
            first_alt = first_alt.split("(")[0].strip()
        # Убираем архитектуру (:amd64)
        if ":" in first_alt:
            first_alt = first_alt.split(":")[0].strip()
            
        if first_alt:
            dependencies.append(first_alt)
            
    return dependencies


def get_direct_dependencies(config: dict) -> list:
    """Fetch data and find direct dependencies for the target package."""
    print(f"Fetching data from {config['repo_url']}...")
    raw_content = fetch_repo_data(config["repo_url"])
    packages = parse_packages_file(raw_content)
    
    target_name = config["package_name"]
    target_ver = config["package_version"]
    
    for pkg in packages:
        pkg_name = pkg.get("Package")
        pkg_ver = pkg.get("Version")
        
        if pkg_name == target_name and pkg_ver == target_ver:
            depends_str = pkg.get("Depends", "")
            return parse_depends_string(depends_str)
            
    raise ConfigError(
        f"Package '{target_name}' version '{target_ver}' not found."
    )


def print_parameters(params: dict) -> None:
    """Print parameters in key-value format."""
    print("=== Configuration Parameters ===")
    for key, value in params.items():
        print(f"{key}: {value}")
    print("=================================")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer. Stage 2."
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
        
        if valid_config["repo_mode"] == "real":
            deps = get_direct_dependencies(valid_config)
            print(f"\nDirect dependencies for {valid_config['package_name']}"
                  f" ({valid_config['package_version']}):")
            for dep in deps:
                print(f" - {dep}")
        else:
            print("Test mode is not implemented yet (Stage 3).")
            
    except ConfigError as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()