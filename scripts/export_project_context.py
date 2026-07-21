#!/usr/bin/env python3

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "context_exports"

CONTEXT_PATH = EXPORT_DIR / "project_context_full.txt"
ZIP_PATH = (
    EXPORT_DIR
    / "alberta-electricity-price-predictor.zip"
)
MANIFEST_PATH = (
    EXPORT_DIR
    / "project_files_manifest.txt"
)
EXCLUDED_PATH = (
    EXPORT_DIR
    / "project_excluded_manifest.txt"
)

MAX_INLINE_TEXT_BYTES = 2 * 1024 * 1024

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".parcel-cache",
    ".turbo",
    ".next",
    "context_exports",
    "local",
    "logs",
}

EXCLUDED_FILENAMES = {
    ".DS_Store",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".env.development.local",
    ".env.production.local",
    ".env.test.local",
}

SECRET_PATTERNS = {
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_rsa.*",
    "credentials.json",
    "service-account*.json",
}

KNOWN_TEXT_NAMES = {
    "Makefile",
    "Dockerfile",
    "Procfile",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    ".npmrc",
    ".nvmrc",
    ".python-version",
}

KNOWN_TEXT_SUFFIXES = {
    ".bash",
    ".cjs",
    ".conf",
    ".css",
    ".csv",
    ".dockerfile",
    ".env.example",
    ".gitkeep",
    ".graphql",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".lock",
    ".md",
    ".mjs",
    ".prisma",
    ".properties",
    ".py",
    ".rst",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}


@dataclass(frozen=True)
class ProjectFile:
    absolute_path: Path
    relative_path: Path
    size_bytes: int
    sha256: str
    kind: str


def run_command(
    command: list[str],
) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        return f"Command unavailable: {error}"

    output = result.stdout

    if result.stderr:
        output += result.stderr

    return output.rstrip()


def exclusion_reason(
    relative_path: Path,
) -> str | None:
    if any(
        part in EXCLUDED_DIRECTORIES
        for part in relative_path.parts
    ):
        return "generated/dependency directory"

    if relative_path.name in EXCLUDED_FILENAMES:
        return "environment or secret file"

    for pattern in SECRET_PATTERNS:
        if fnmatch.fnmatch(
            relative_path.name,
            pattern,
        ):
            return "credential or private key"

    return None


def calculate_sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def is_text_file(
    path: Path,
) -> bool:
    if path.name in KNOWN_TEXT_NAMES:
        return True

    suffixes = "".join(path.suffixes).lower()

    if (
        suffixes in KNOWN_TEXT_SUFFIXES
        or path.suffix.lower()
        in KNOWN_TEXT_SUFFIXES
    ):
        return True

    try:
        sample = path.read_bytes()[:65536]
    except OSError:
        return False

    if b"\x00" in sample:
        return False

    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False

    return True


def collect_project_files() -> tuple[
    list[ProjectFile],
    list[tuple[str, str]],
]:
    project_files: list[ProjectFile] = []
    excluded: list[tuple[str, str]] = []

    for current_root, directories, filenames in os.walk(
        ROOT,
    ):
        current_path = Path(current_root)
        relative_directory = current_path.relative_to(
            ROOT,
        )

        kept_directories: list[str] = []

        for directory in directories:
            relative_path = (
                relative_directory / directory
            )

            reason = exclusion_reason(relative_path)

            if reason:
                excluded.append(
                    (
                        f"{relative_path}/",
                        reason,
                    )
                )
            else:
                kept_directories.append(directory)

        directories[:] = kept_directories

        for filename in filenames:
            absolute_path = current_path / filename
            relative_path = absolute_path.relative_to(
                ROOT,
            )

            reason = exclusion_reason(relative_path)

            if reason:
                excluded.append(
                    (
                        str(relative_path),
                        reason,
                    )
                )
                continue

            if not absolute_path.is_file():
                continue

            size_bytes = absolute_path.stat().st_size
            kind = (
                "text"
                if is_text_file(absolute_path)
                else "binary"
            )

            project_files.append(
                ProjectFile(
                    absolute_path=absolute_path,
                    relative_path=relative_path,
                    size_bytes=size_bytes,
                    sha256=calculate_sha256(
                        absolute_path,
                    ),
                    kind=kind,
                )
            )

    project_files.sort(
        key=lambda item: str(
            item.relative_path,
        ).lower()
    )

    excluded.sort(
        key=lambda item: item[0].lower()
    )

    return project_files, excluded


def write_manifests(
    files: list[ProjectFile],
    excluded: list[tuple[str, str]],
) -> None:
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_lines = [
        "path\tsize_bytes\tsha256\tkind"
    ]

    for item in files:
        manifest_lines.append(
            "\t".join(
                [
                    str(item.relative_path),
                    str(item.size_bytes),
                    item.sha256,
                    item.kind,
                ]
            )
        )

    MANIFEST_PATH.write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )

    excluded_lines = [
        "path\treason"
    ]

    for path, reason in excluded:
        excluded_lines.append(
            f"{path}\t{reason}"
        )

    EXCLUDED_PATH.write_text(
        "\n".join(excluded_lines) + "\n",
        encoding="utf-8",
    )


def append_command_section(
    output: list[str],
    title: str,
    command: list[str],
) -> None:
    output.extend(
        [
            "",
            f"===== {title} =====",
            run_command(command),
        ]
    )


def large_text_preview(
    path: Path,
) -> str:
    try:
        with path.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as stream:
            first_lines: list[str] = []

            for _ in range(20):
                line = stream.readline()

                if not line:
                    break

                first_lines.append(line.rstrip())

        return "\n".join(
            [
                "[Large text file: full content is in the ZIP]",
                "",
                "----- FIRST 20 LINES -----",
                *first_lines,
            ]
        )
    except OSError as error:
        return f"[Unable to preview file: {error}]"


def write_context(
    files: list[ProjectFile],
    excluded: list[tuple[str, str]],
) -> None:
    output: list[str] = [
        "===== PROJECT CONTEXT GENERATED AT =====",
        datetime.now().astimezone().isoformat(),
        "",
        "===== EXPORT POLICY =====",
        (
            "This export includes all project-relevant "
            "files regardless of Git ignore status."
        ),
        (
            "Only dependency directories, generated "
            "builds, caches, Git metadata, virtual "
            "environments, export outputs, and likely "
            "secret files are excluded."
        ),
        (
            "Large text files and binary files are "
            "represented in this document by metadata "
            "and are included in the ZIP archive."
        ),
        "",
        "===== EXPORT SUMMARY =====",
        f"Included files: {len(files)}",
        f"Excluded paths: {len(excluded)}",
        (
            "Inline text limit: "
            f"{MAX_INLINE_TEXT_BYTES} bytes"
        ),
    ]

    append_command_section(
        output,
        "BRANCH",
        ["git", "branch", "--show-current"],
    )

    append_command_section(
        output,
        "HEAD COMMIT",
        ["git", "log", "-1", "--decorate", "--oneline"],
    )

    append_command_section(
        output,
        "GIT STATUS",
        ["git", "status", "--short"],
    )

    append_command_section(
        output,
        "GIT STATUS INCLUDING IGNORED FILES",
        [
            "git",
            "status",
            "--short",
            "--ignored",
        ],
    )

    append_command_section(
        output,
        "GIT DIFF STAT",
        ["git", "diff", "--stat"],
    )

    append_command_section(
        output,
        "GIT DIFF",
        [
            "git",
            "diff",
            "--",
            ".",
            ":(exclude)reports/*.csv",
        ],
    )

    append_command_section(
        output,
        "RECENT COMMITS",
        ["git", "log", "--oneline", "-20"],
    )

    append_command_section(
        output,
        "PYTHON VERSION",
        ["python3", "--version"],
    )

    append_command_section(
        output,
        "NODE VERSION",
        ["node", "--version"],
    )

    append_command_section(
        output,
        "NPM VERSION",
        ["npm", "--version"],
    )

    append_command_section(
        output,
        "DOCKER VERSION",
        ["docker", "--version"],
    )

    output.extend(
        [
            "",
            "===== INCLUDED FILE INVENTORY =====",
            MANIFEST_PATH.read_text(
                encoding="utf-8",
            ).rstrip(),
            "",
            "===== INTENTIONALLY EXCLUDED PATHS =====",
            EXCLUDED_PATH.read_text(
                encoding="utf-8",
            ).rstrip(),
            "",
            "===== FILE CONTENTS =====",
        ]
    )

    for item in files:
        output.extend(
            [
                "",
                (
                    "===== "
                    f"{item.relative_path} "
                    "====="
                ),
                (
                    "["
                    f"size={item.size_bytes}; "
                    f"sha256={item.sha256}; "
                    f"kind={item.kind}"
                    "]"
                ),
            ]
        )

        if item.kind == "binary":
            output.append(
                (
                    "[Binary file: full file is "
                    "included in the ZIP archive]"
                )
            )
            continue

        if (
            item.size_bytes
            > MAX_INLINE_TEXT_BYTES
        ):
            output.append(
                large_text_preview(
                    item.absolute_path,
                )
            )
            continue

        try:
            content = item.absolute_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            output.append(
                f"[Unable to read file: {error}]"
            )
            continue

        output.append(content.rstrip())

    CONTEXT_PATH.write_text(
        "\n".join(output) + "\n",
        encoding="utf-8",
    )


def write_zip(
    files: list[ProjectFile],
) -> None:
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(
        ZIP_PATH,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for item in files:
            archive.write(
                item.absolute_path,
                arcname=str(item.relative_path),
            )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices={
            "context",
            "zip",
            "all",
        },
        default="all",
    )

    arguments = parser.parse_args()

    files, excluded = collect_project_files()

    write_manifests(files, excluded)

    if arguments.mode in {
        "context",
        "all",
    }:
        write_context(files, excluded)

    if arguments.mode in {
        "zip",
        "all",
    }:
        write_zip(files)

    print(
        f"Included project files: {len(files)}"
    )

    if CONTEXT_PATH.exists():
        print(
            "Text context: "
            f"{CONTEXT_PATH.relative_to(ROOT)}"
        )

    if ZIP_PATH.exists():
        print(
            "ZIP archive: "
            f"{ZIP_PATH.relative_to(ROOT)}"
        )

    print(
        "Included manifest: "
        f"{MANIFEST_PATH.relative_to(ROOT)}"
    )

    print(
        "Excluded manifest: "
        f"{EXCLUDED_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
