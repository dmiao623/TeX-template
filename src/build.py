"""CLI entrypoint for assembling a TeX preamble from macro definitions."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from src.parser import (
    load_commands,
    load_modifiers,
    parse_macros_file,
    parse_tex_commands,
)
from src.utils import FileBuilder


def main(
    tex_commands_path: Path,
    macros_path: Path,
    preamble_path: Path,
    output_path: Path,
    main_path: Path,
    config_path: Path,
    no_test: bool = False,
) -> None:
    """Assemble a TeX preamble by combining a base preamble with macro definitions.

    Args:
        tex_commands_path: Path to the LaTeX commands list file.
        macros_path: Path to the YAML macros configuration file.
        preamble_path: Path to the base preamble.tex file.
        output_path: Path to write the assembled output.
        main_path: Path to the main .tex file to copy into the build directory.
        config_path: Path to the config .tex file to copy into the build directory.
        no_test: If True, skip compiling the resulting build.
    """
    tex_commands = parse_tex_commands(tex_commands_path)
    macros = parse_macros_file(macros_path)

    preamble_fp = FileBuilder(preamble_path)
    modifier_fp = load_modifiers(tex_commands, macros["modifiers"])
    command_fp = load_commands(tex_commands, macros["commands"])

    (
        preamble_fp
        .add_file_builder(modifier_fp)
        .add_file_builder(command_fp)
        .save(output_path)
    )

    build_dir = output_path.parent
    shutil.copy2(main_path, build_dir / main_path.name)
    shutil.copy2(config_path, build_dir / config_path.name)

    if not no_test:
        compile_build(build_dir, main_path.name)


def compile_build(
    build_dir: Path,
    main_filename: str
) -> None:
    """Compile the TeX project and report any errors."""
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", main_filename],
        cwd=build_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("LaTeX compilation failed. Errors:", file=sys.stderr)
        for line in result.stdout.splitlines():
            if line.startswith("!"):
                print(line, file=sys.stderr)
        sys.exit(result.returncode)
    else:
        print("LaTeX compilation executed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Assemble a TeX preamble from macro definitions."
    )
    parser.add_argument(
        "--tex-commands",
        type=Path,
        default=Path("data/latex-commands.txt"),
        help="Path to the LaTeX commands list (default: data/latex-commands.txt)",
    )
    parser.add_argument(
        "--macros",
        type=Path,
        default=Path("data/macros.yaml"),
        help="Path to the YAML macros file (default: data/macros.yaml)",
    )
    parser.add_argument(
        "--preamble",
        type=Path,
        default=Path("data/preamble-base.tex"),
        help="Path to the base preamble.tex file (default: preamble-base.tex)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/preamble.tex"),
        help="Path to write the assembled output (default: data/preamble.tex)",
    )
    parser.add_argument(
        "--main",
        type=Path,
        default=Path("data/main.tex"),
        help="Path to the main .tex file (default: data/main.tex)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data/config.tex"),
        help="Path to the config .tex file (default: data/config.tex)",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip compiling the resulting build.",
    )

    args = parser.parse_args()
    main(
        args.tex_commands, args.macros, args.preamble, args.output,
        args.main, args.config, args.no_test,
    )
