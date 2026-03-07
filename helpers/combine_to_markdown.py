#!/usr/bin/env python3
"""
Combine all relevant files from the solution into a single markdown document.
Useful for providing a complete codebase overview to AI agents.

Organizes files in the following order:
1. Folder structure overview
2. Markdown and text files
3. Python files
4. Other files (shell scripts, nix files, etc.)
"""

import os
import argparse
from pathlib import Path


# Folders to exclude from processing
EXCLUDED_DIRS = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}

# File extensions to include
MARKDOWN_EXTENSIONS = {'.md', '.markdown'}
TEXT_EXTENSIONS = {'.txt', '.rst', '.log'}
PYTHON_EXTENSIONS = {'.py'}
OTHER_RELEVANT_EXTENSIONS = {'.sh', '.nix', '.yml', '.yaml', '.json', '.toml', '.ini', '.cfg', '.gitignore', '.dockerfile'}


def generate_folder_structure(base_path: Path) -> str:
    """Generate a tree-like folder structure overview."""
    lines = ["# Folder Structure Overview", "", "```"]
    
    def walk_dir(path: Path, prefix: str = "", is_last: bool = True):
        """Recursively walk directory and generate tree structure."""
        # Get all items, sorted by type (dirs first) then name
        items = sorted(
            path.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower())
        )
        
        for i, item in enumerate(items):
            if item.name in EXCLUDED_DIRS:
                continue
                
            is_last_item = (i == len(items) - 1)
            connector = "└── " if is_last_item else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                # Add files in directory (limit to first 5 for overview)
                sub_items = sorted([p for p in item.iterdir() if p.name not in EXCLUDED_DIRS])
                if sub_items:
                    extension_prefix = "    " if is_last_item else "│   "
                    for j, sub_item in enumerate(sub_items[:5]):
                        sub_connector = "└── " if j == len(sub_items[:5]) - 1 else "├── "
                        lines.append(f"{prefix}{extension_prefix}{sub_connector}{sub_item.name}")
                    if len(sub_items) > 5:
                        lines.append(f"{prefix}{extension_prefix}    ... ({len(sub_items) - 5} more)")
            else:
                lines.append(f"{prefix}{connector}{item.name}")
    
    # Start from base path
    lines.append(base_path.name + "/")
    walk_dir(base_path, "", True)
    
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


def collect_files_by_type(base_path: Path) -> dict:
    """
    Collect all relevant files organized by type.
    Returns dict with keys: 'markdown', 'text', 'python', 'other'
    """
    files = {
        'markdown': [],
        'text': [],
        'python': [],
        'other': []
    }
    
    def should_exclude(path: Path) -> bool:
        """Check if path should be excluded."""
        # Check if any parent directory is in excluded list
        for parent in path.parents:
            if parent.name in EXCLUDED_DIRS:
                return True
        return False
    
    for path in base_path.rglob("*"):
        if path.is_file() and not should_exclude(path):
            # Skip the output file itself
            if path.name.endswith('.md') and path.name.startswith('codebase'):
                continue
                
            suffix = path.suffix.lower()
            display_name = str(path.relative_to(base_path))
            
            if suffix in MARKDOWN_EXTENSIONS:
                files['markdown'].append((display_name, path))
            elif suffix in TEXT_EXTENSIONS:
                files['text'].append((display_name, path))
            elif suffix in PYTHON_EXTENSIONS:
                files['python'].append((display_name, path))
            elif suffix in OTHER_RELEVANT_EXTENSIONS or path.name in {'.gitignore', 'Dockerfile', 'Makefile'}:
                files['other'].append((display_name, path))
    
    # Sort each category
    for category in files:
        files[category].sort(key=lambda x: x[0].lower())
    
    return files


def read_file(path: Path) -> str:
    """Read file contents as string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            return f"[Error reading file: {e}]"
    except Exception as e:
        return f"[Error reading file: {e}]"


def get_language_for_extension(filename: str) -> str:
    """Map file extension to language for code highlighting."""
    ext = Path(filename).suffix.lower()
    
    language_map = {
        '.py': 'python',
        '.md': 'markdown',
        '.sh': 'bash',
        '.nix': 'nix',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.rst': 'rst',
        '.txt': 'text',
        '.gitignore': 'gitignore',
    }
    
    return language_map.get(ext, '')


def generate_file_section(files: list[tuple[str, Path]], section_title: str) -> str:
    """Generate markdown section for a list of files."""
    if not files:
        return ""
    
    lines = [
        f"## {section_title}",
        "",
        f"> {len(files)} files",
        ""
    ]
    
    for display_name, file_path in files:
        content = read_file(file_path)
        language = get_language_for_extension(display_name)
        
        lines.extend([
            f"### `{display_name}`",
            "",
            f"```{language}",
            content.rstrip(),  # Remove trailing whitespace
            "```",
            "",
            "---",
            ""
        ])
    
    return "\n".join(lines)


def generate_markdown(base_path: Path, files: dict, title: str = "Solution Codebase") -> str:
    """Generate complete markdown document."""
    md_lines = [
        f"# {title}",
        "",
        f"> Generated from solution at: `{base_path}`",
        "",
        "---",
        "",
    ]
    
    # 1. Folder structure overview
    md_lines.append(generate_folder_structure(base_path))
    md_lines.append("---")
    md_lines.append("")
    
    # 2. Markdown and text files
    text_files = files['markdown'] + files['text']
    if text_files:
        md_lines.append(generate_file_section(text_files, "Markdown & Text Files"))
    
    # 3. Python files
    if files['python']:
        md_lines.append(generate_file_section(files['python'], "Python Files"))
    
    # 4. Other files
    if files['other']:
        md_lines.append(generate_file_section(files['other'], "Other Files"))
    
    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Combine all relevant solution files into a single markdown document"
    )
    parser.add_argument(
        "-o", "--output",
        default="codebase.md",
        help="Output markdown file (default: codebase.md)"
    )
    parser.add_argument(
        "--title",
        default="Solution Codebase",
        help="Title for the markdown document"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Base path to scan (default: current directory)"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional directories to exclude"
    )
    
    args = parser.parse_args()
    
    # Add custom exclusions
    global EXCLUDED_DIRS
    EXCLUDED_DIRS = EXCLUDED_DIRS.union(set(args.exclude))
    
    base_path = Path(args.path).resolve()
    output_path = base_path / args.output
    
    print(f"Scanning: {base_path}")
    print(f"Output: {output_path}")
    print(f"Excluded dirs: {EXCLUDED_DIRS}")
    print()
    
    # Collect all files
    files = collect_files_by_type(base_path)
    
    total_files = sum(len(files[cat]) for cat in files)
    
    if total_files == 0:
        print("ERROR: No files found!")
        return 1
    
    print(f"Found {total_files} files:")
    print(f"  - Markdown files: {len(files['markdown'])}")
    print(f"  - Text files: {len(files['text'])}")
    print(f"  - Python files: {len(files['python'])}")
    print(f"  - Other files: {len(files['other'])}")
    print()
    
    # Print file list
    print("Files to be combined:")
    for category, file_list in files.items():
        if file_list:
            print(f"\n  {category.upper()}:")
            for name, _ in file_list:
                print(f"    - {name}")
    print()
    
    # Generate markdown
    markdown = generate_markdown(base_path, files, args.title)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✓ Created: {output_path}")
    print(f"  Size: {len(markdown):,} characters")
    
    return 0


if __name__ == "__main__":
    exit(main())