#!/usr/bin/env python3
"""
Combine main.py, all modules/*.py files, and all data/*.md files into a single markdown document.
Useful for providing a complete codebase overview to AI agents.
"""

import os
import argparse
from pathlib import Path


def get_python_files(base_path: Path, modules_folder: str = "modules") -> list[tuple[str, Path]]:
    """
    Collect main.py and all .py files from the modules folder.
    Returns list of (display_name, full_path) tuples.
    """
    files = []
    
    # Add main.py
    main_path = base_path / "main.py"
    if main_path.exists():
        files.append(("main.py", main_path))
    
    # Add all modules/*.py
    modules_path = base_path / modules_folder
    if modules_path.exists():
        for py_file in sorted(modules_path.glob("*.py")):
            files.append((f"modules/{py_file.name}", py_file))
    
    return files


def get_markdown_files(base_path: Path, data_folder: str = "data") -> list[tuple[str, Path]]:
    """
    Collect all .md files from the data folder.
    Returns list of (display_name, full_path) tuples.
    """
    files = []
    
    # Add all data/*.md
    data_path = base_path / data_folder
    if data_path.exists():
        for md_file in sorted(data_path.glob("*.md")):
            files.append((f"data/{md_file.name}", md_file))
    
    return files


def read_file(path: Path) -> str:
    """Read file contents as string."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_markdown(files: list[tuple[str, Path]], title: str = "AAIA Codebase") -> str:
    """Generate markdown document with all files."""
    md_lines = [
        f"# {title}",
        "",
        f"> Combined from {len(files)} files (Python and Markdown)",
        "",
        "---",
        ""
    ]
    
    for display_name, file_path in files:
        content = read_file(file_path)
        
        # Determine language for code block based on file extension
        if display_name.endswith('.py'):
            language = 'python'
        elif display_name.endswith('.md'):
            language = 'markdown'
        else:
            language = ''
        
        md_lines.extend([
            f"## `{display_name}`",
            "",
            f"```{language}",
            content,
            "```",
            "",
            "---",
            ""
        ])
    
    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Combine main.py, modules/*.py, and data/*.md into a single markdown file"
    )
    parser.add_argument(
        "-o", "--output",
        default="codebase.md",
        help="Output markdown file (default: codebase.md)"
    )
    parser.add_argument(
        "-m", "--modules",
        default="modules",
        help="Modules folder name (default: modules)"
    )
    parser.add_argument(
        "-d", "--data",
        default="data",
        help="Data folder name (default: data)"
    )
    parser.add_argument(
        "--title",
        default="AAIA Codebase",
        help="Title for the markdown document"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Base path to search for main.py, modules folder, and data folder"
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.path).resolve()
    output_path = base_path / args.output
    
    print(f"Scanning: {base_path}")
    print(f"Modules folder: {args.modules}")
    print(f"Data folder: {args.data}")
    
    python_files = get_python_files(base_path, args.modules)
    markdown_files = get_markdown_files(base_path, args.data)
    
    all_files = markdown_files + python_files
    
    if not all_files:
        print("ERROR: No files found!")
        return 1
    
    print(f"Found {len(all_files)} files:")
    for name, _ in all_files:
        print(f"  - {name}")
    
    markdown = generate_markdown(all_files, args.title)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"\n✓ Created: {output_path}")
    print(f"  Size: {len(markdown):,} characters")
    
    return 0


if __name__ == "__main__":
    exit(main())