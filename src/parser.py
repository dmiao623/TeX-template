"""Parser for TeX macro definitions from YAML configuration files."""

import logging
import string
import yaml
from pathlib import Path
from typing import Any, Dict, List, Set

from src.utils import FileBuilder

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("filebuilder.log"),
        logging.StreamHandler(),
    ],
)


def parse_tex_commands(file_path: Path) -> Set[str]:
    """Parse a file of TeX command names into a set.

    Args:
        file_path: Path to a text file with one command per line.

    Returns:
        A set of command name strings.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        error_msg = f"FileNotFoundError: File '{file_path}' not found."
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    with file_path.open("r") as file:
        return {line.strip() for line in file}


def parse_macros_file(file_path: Path) -> Any:
    """Parse a YAML macros configuration file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        The parsed YAML data structure.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    with file_path.open("r") as file:
        try:
            return yaml.safe_load(file)
        except FileNotFoundError:
            error_msg = f"FileNotFoundError: File '{file_path}' not found."
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        except yaml.YAMLError:
            error_msg = f"YAMLError: Failed to parse file '{file_path}'."
            logging.error(error_msg)
            raise yaml.YAMLError(error_msg)


def load_macro(
    fp: FileBuilder,
    macro_name: str,
    macro_value: str,
    tex_commands: Set[str],
) -> None:
    """Load a single macro definition into a FileBuilder.

    Generates either a \\newcommand/\\renewcommand or a \\DeclareMathOperator
    depending on whether macro_name starts with a backslash.

    Args:
        fp: The FileBuilder to append the macro definition to.
        macro_name: The macro name (e.g. "\\foo" or "operatorname*").
        macro_value: The macro body, possibly containing #1, #2, etc.
        tex_commands: Set of existing TeX commands (used to decide new vs renew).
    """
    num_arguments = 0
    while f"#{num_arguments + 1}" in macro_value:
        num_arguments += 1

    if macro_name[0] == "\\":
        # \(re)newcommand
        body = (
            f"{{{macro_name}}}"
            + ("" if num_arguments == 0 else f"[{num_arguments}]")
            + f"{{{macro_value}}}"
        )
        if macro_name in tex_commands:
            command = "\\renewcommand"
            logging.info(
                f"loaded command '{macro_name}' with value "
                f"'{macro_value}', overrided old binding."
            )
        else:
            command = "\\newcommand"
            logging.info(
                f"loaded command '{macro_name}' with value '{macro_value}'."
            )
        fp.add_line(command + body)
    else:
        # \DeclareMathOperator
        logging.info(
            f"loaded math operator '{macro_name}' with value '{macro_value}'."
        )
        command = (
            "\\DeclareMathOperator" + ("*" if macro_name[-1] == "*" else "")
        )
        fp.add_line(
            f"\\DeclareMathOperator{{\\{macro_name}}}{{{macro_value[:-1]}}}"
        )


def load_modifiers(
    tex_commands: Set[str],
    modifiers: List[Dict[str, str]],
) -> FileBuilder:
    """Generate TeX modifier commands for character ranges.

    Each modifier defines a command (e.g. \\mathbb), a prefix, and a domain
    of characters (e.g. "a-z", "A-Z") to generate macros for.

    Args:
        tex_commands: Set of existing TeX commands.
        modifiers: List of modifier dicts with "command", "prefix", "domain" keys.

    Returns:
        A FileBuilder containing the generated modifier definitions.

    Raises:
        KeyError: If a modifier dict is missing required keys.
    """
    output = FileBuilder()
    for modifier in modifiers:
        try:
            command = modifier["command"]
            prefix = modifier["prefix"]
            domain = modifier["domain"]
        except KeyError:
            error_msg = "KeyError: modifier is ill-formed."
            logging.error(error_msg)
            raise KeyError(error_msg)

        output.add_new_line()
        output.add_line(f"% {command}")

        domain_chars: list[str] = []
        if "a-z" in domain:
            domain_chars.extend(list(string.ascii_lowercase))
        if "A-Z" in domain:
            domain_chars.extend(list(string.ascii_uppercase))

        for char in domain_chars:
            macro_name = "\\" + prefix + char
            macro_value = f"{command}{{{char}}}"
            load_macro(output, macro_name, macro_value, tex_commands)

    return output


def load_commands(
    tex_commands: Set[str],
    commands: Dict[str, List[Dict[str, str]]],
) -> FileBuilder:
    """Generate TeX command definitions grouped by category.

    Args:
        tex_commands: Set of existing TeX commands.
        commands: Nested dict mapping group names to lists of macro definitions.

    Returns:
        A FileBuilder containing the generated command definitions.
    """
    output = FileBuilder()
    groups = sorted(commands.keys())
    for group in groups:
        output.add_new_line()
        output.add_line(f"% {group}")

        for macro in commands[group]:
            macro_name = str(next(iter(macro)))
            macro_value = macro[macro_name]
            load_macro(output, macro_name, macro_value, tex_commands)

    return output