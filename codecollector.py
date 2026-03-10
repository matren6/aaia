#!/usr/bin/env python3
"""
Interactive file selector with curses interface for combining files into markdown.
Based on combine_to_markdown.py but with interactive selection capabilities.
Enhanced with yellow highlighting, optional selections, and condensed Python export.
"""

import os
import argparse
import curses
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set


# Folders to exclude from processing
EXCLUDED_DIRS = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}

# File extensions to include
MARKDOWN_EXTENSIONS = {'.md', '.markdown'}
TEXT_EXTENSIONS = {'.txt', '.rst', '.log'}
PYTHON_EXTENSIONS = {'.py'}
OTHER_RELEVANT_EXTENSIONS = {'.sh', '.nix', '.yml', '.yaml', '.json', '.toml', '.ini', '.cfg', '.gitignore', '.dockerfile'}


class FileNode:
    """Represents a file or folder in the file tree."""
    
    def __init__(self, path: Path, parent=None):
        self.path = path
        self.parent = parent
        self.children = []
        self.is_dir = path.is_dir()
        self.is_selected = False
        self.is_expanded = False
        self.depth = 0
        
        if parent:
            self.depth = parent.depth + 1
    
    def add_child(self, child):
        """Add a child node."""
        child.parent = self
        child.depth = self.depth + 1
        self.children.append(child)
    
    def toggle_selection(self):
        """Toggle selection for this node and its children."""
        self.is_selected = not self.is_selected
        if self.is_dir:
            for child in self.children:
                child.is_selected = self.is_selected
    
    def toggle_expansion(self):
        """Toggle expansion for directories."""
        if self.is_dir:
            self.is_expanded = not self.is_expanded
    
    def expand(self):
        """Expand this directory."""
        if self.is_dir:
            self.is_expanded = True
    
    def collapse(self):
        """Collapse this directory."""
        if self.is_dir:
            self.is_expanded = False
    
    def get_display_name(self, show_all_files=False):
        """Get the display name with appropriate prefix."""
        name = self.path.name
        if self.is_dir:
            name += "/"
        
        # Add prefix based on depth
        prefix = ""
        if self.depth > 0:
            prefix = "  " * self.depth
        
        # Add expansion indicator for directories
        if self.is_dir:
            if self.is_expanded:
                prefix += "▼ "
            else:
                prefix += "▶ "
        
        # Add selection indicator
        if self.is_selected:
            prefix += "[✓] "
        else:
            prefix += "[ ] "
        
        # Add indicator for unselected files when show_all_files is enabled
        if show_all_files and not self.is_dir and not self.is_selected:
            prefix += "(not included) "
        
        return prefix + name
    
    def is_visible(self, show_all_files=False):
        """Check if this node should be visible in the tree."""
        if self.depth == 0:
            return True
        
        # If any parent is not expanded, this node is not visible
        parent = self.parent
        while parent:
            if parent.is_dir and not parent.is_expanded:
                return False
            parent = parent.parent
        
        # If show_all_files is False, hide unselected files
        if not show_all_files and not self.is_dir and not self.is_selected:
            return False
        
        return True


class FileTree:
    """Manages the file tree structure."""
    
    def __init__(self, base_path: Path, show_all_files=False):
        self.base_path = base_path
        self.root = FileNode(base_path)
        self.nodes = []
        self.show_all_files = show_all_files
        self.build_tree()
    
    def build_tree(self):
        """Build the file tree from the base path."""
        def build_node(parent: FileNode, path: Path):
            node = FileNode(path, parent)
            parent.add_child(node)
            
            if path.is_dir():
                # Add children
                items = sorted(
                    path.iterdir(),
                    key=lambda x: (not x.is_dir(), x.name.lower())
                )
                
                for item in items:
                    if item.name in EXCLUDED_DIRS:
                        continue
                    build_node(node, item)
            
            return node
        
        # Build tree recursively
        items = sorted(
            self.base_path.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower())
        )
        
        for item in items:
            if item.name in EXCLUDED_DIRS:
                continue
            build_node(self.root, item)
        
        # Expand root by default
        self.root.is_expanded = True
        self.update_visible_nodes()
            
    def update_visible_nodes(self, selected_node=None):
        """Update the list of visible nodes and return the index of the selected node."""
        self.nodes = []
        selected_index = -1
        
        def collect_visible(node: FileNode):
            nonlocal selected_index
            if node.is_visible(self.show_all_files):
                if selected_node and node.path == selected_node.path:
                    selected_index = len(self.nodes)
                self.nodes.append(node)
                
                if node.is_dir and node.is_expanded:
                    for child in node.children:
                        collect_visible(child)
        
        for child in self.root.children:
            collect_visible(child)
        
        return selected_index

    def toggle_selection(self, index: int):
        """Toggle selection for a node by index."""
        if 0 <= index < len(self.nodes):
            node = self.nodes[index]
            node.toggle_selection()
            selected_node = self.nodes[index]  # Remember the selected node
            self.update_visible_nodes(selected_node)
            return True
        return False

    def toggle_expansion(self, index: int):
        """Toggle expansion for a directory by index."""
        if 0 <= index < len(self.nodes):
            node = self.nodes[index]
            if node.is_dir:
                node.toggle_expansion()
                selected_node = self.nodes[index]  # Remember the selected node
                self.update_visible_nodes(selected_node)
                return True
        return False

    def expand_node(self, index: int):
        """Expand a directory by index."""
        if 0 <= index < len(self.nodes):
            node = self.nodes[index]
            if node.is_dir:
                node.expand()
                selected_node = self.nodes[index]  # Remember the selected node
                self.update_visible_nodes(selected_node)
                return True
        return False

    def collapse_node(self, index: int):
        """Collapse a directory by index."""
        if 0 <= index < len(self.nodes):
            node = self.nodes[index]
            if node.is_dir:
                node.collapse()
                selected_node = self.nodes[index]  # Remember the selected node
                self.update_visible_nodes(selected_node)
                return True
        return False

    def select_all(self):
        """Select all nodes."""
        def select_recursive(node: FileNode):
            node.is_selected = True
            if node.is_dir:
                for child in node.children:
                    select_recursive(child)
        
        for child in self.root.children:
            select_recursive(child)
        self.update_visible_nodes()
        return True

    def deselect_all(self):
        """Deselect all nodes."""
        def deselect_recursive(node: FileNode):
            node.is_selected = False
            if node.is_dir:
                for child in node.children:
                    deselect_recursive(child)
        
        for child in self.root.children:
            deselect_recursive(child)
        self.update_visible_nodes()
        return True

    def toggle_show_all_files(self, selected_index=0):
        """Toggle the show_all_files option."""
        self.show_all_files = not self.show_all_files
        selected_node = self.nodes[selected_index] if selected_index < len(self.nodes) else None
        return self.update_visible_nodes(selected_node)
            
    def get_selected_files(self) -> List[Path]:
        """Get all selected file paths."""
        selected = []
        
        def collect_selected(node: FileNode):
            if node.is_selected and not node.is_dir:
                selected.append(node.path)
            if node.is_dir:
                for child in node.children:
                    collect_selected(child)
        
        for child in self.root.children:
            collect_selected(child)
        
        return selected
    
    def get_all_python_files(self) -> List[Path]:
        """Get all Python file paths, both selected and unselected."""
        python_files = []
        
        def collect_python(node: FileNode):
            if not node.is_dir and node.path.suffix.lower() == '.py':
                python_files.append(node.path)
            if node.is_dir:
                for child in node.children:
                    collect_python(child)
        
        for child in self.root.children:
            collect_python(child)
        
        return python_files


class FileSelectorApp:
    """Main application class for the file selector."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.file_tree = FileTree(base_path)
        self.selected_index = 0
        self.viewport_start = 0  # Add this line - persist viewport position
        self.running = True
        self.should_generate = False
        self.needs_redraw = True
        self.condensed_python = True
        self.show_all_files = True

    def run(self):
        """Run the application."""
        curses.wrapper(self._run)
    
    def _run(self, stdscr):
        """Run the application with curses."""
        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Directory
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Selected item
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Help text
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Active item
        
        # Hide cursor
        curses.curs_set(0)
        
        # Enable keyboard input with blocking mode
        stdscr.nodelay(0)  # Changed from 1 to 0 for blocking input
        stdscr.clear()
        
        while self.running:
            if self.needs_redraw:
                self._draw(stdscr)
                self.needs_redraw = False
            
            # Wait for input (blocking)
            key = stdscr.getch()
            self._handle_input(stdscr, key)

    def _draw(self, stdscr):
        """Draw the interface."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Draw title
        title = f"File Selector - {self.base_path}"
        stdscr.addstr(0, 0, title, curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * min(width, len(title)))
        
        # Draw options status
        options_line = f"Options: Show All Files: {'ON' if self.show_all_files else 'OFF'} | Condensed Python: {'ON' if self.condensed_python else 'OFF'}"
        stdscr.addstr(2, 0, options_line, curses.color_pair(4))
        
        # Draw file tree
        start_y = 4
        # FIX: Calculate viewport_height correctly
        # Help text starts at height - 5, so file tree can use y from start_y to height - 6
        # Number of available rows = (height - 6) - start_y + 1 = height - start_y - 5
        viewport_height = max(1, height - start_y - 5)
        
        visible_nodes = self.file_tree.nodes
        total_items = len(visible_nodes)
        
        # Ensure viewport_start is valid
        if total_items == 0:
            self.viewport_start = 0
        else:
            # Adjust viewport to ensure selected item is always visible
            if self.selected_index < self.viewport_start:
                self.viewport_start = self.selected_index
            elif self.selected_index >= self.viewport_start + viewport_height:
                self.viewport_start = self.selected_index - viewport_height + 1
            
            # Clamp viewport_start to valid range
            max_viewport_start = max(0, total_items - viewport_height)
            self.viewport_start = max(0, min(self.viewport_start, max_viewport_start))
        
        viewport_start = self.viewport_start
        viewport_end = min(viewport_start + viewport_height, total_items)
        
        # Draw visible nodes
        for i in range(viewport_start, viewport_end):
            node = visible_nodes[i]
            y = start_y + (i - viewport_start)
            
            # This check is now redundant but keep for safety
            if y >= height - 5:
                break
            
            # Format display string
            display_str = node.get_display_name(self.show_all_files)
            
            # Truncate if too long
            if len(display_str) > width - 2:
                display_str = display_str[:width-3] + "..."
            
            # Apply colors
            if i == self.selected_index:
                color = curses.color_pair(5) | curses.A_BOLD
            elif node.is_selected:
                color = curses.color_pair(3)
            elif node.is_dir:
                color = curses.color_pair(2)
            elif not node.is_selected and self.show_all_files:
                color = curses.A_DIM
            else:
                color = curses.color_pair(0)
            
            stdscr.addstr(y, 0, display_str, color)
        
        # Draw help text
        help_y = height - 5
        help_text = [
            "SPACE: Toggle selection | ENTER: Toggle directory expansion",
            "A: Select all | D: Deselect all | S: Toggle show all files | P: Toggle condensed Python",
            "↑/↓: Navigate | ←/→: Collapse/Expand | Q: Quit and generate markdown | ESC: Quit without generating"
        ]
        
        for i, text in enumerate(help_text):
            if len(text) > width:
                text = text[:width-1]
            stdscr.addstr(help_y + i, 0, text, curses.color_pair(4))
        
        # Draw status
        selected_count = len(self.file_tree.get_selected_files())
        status = f"Selected: {selected_count} files"
        stdscr.addstr(height - 1, 0, status, curses.A_BOLD)
        
        stdscr.refresh()
                    
    def _handle_input(self, stdscr, key):
        """Handle keyboard input."""
        needs_redraw = False
        
        if key == curses.KEY_UP:
            self.selected_index = max(0, self.selected_index - 1)
            needs_redraw = True
        elif key == curses.KEY_DOWN:
            self.selected_index = min(len(self.file_tree.nodes) - 1, self.selected_index + 1)
            needs_redraw = True
        elif key == curses.KEY_LEFT:
            # Collapse directory
            if 0 <= self.selected_index < len(self.file_tree.nodes):
                node = self.file_tree.nodes[self.selected_index]
                if node.is_dir:
                    node.collapse()
                    selected_node = node  # Remember the selected node
                    self.selected_index = self.file_tree.update_visible_nodes(selected_node)
                    needs_redraw = True
        elif key == curses.KEY_RIGHT:
            # Expand directory
            if 0 <= self.selected_index < len(self.file_tree.nodes):
                node = self.file_tree.nodes[self.selected_index]
                if node.is_dir:
                    node.expand()
                    selected_node = node  # Remember the selected node
                    self.selected_index = self.file_tree.update_visible_nodes(selected_node)
                    needs_redraw = True
        elif key == ord(' '):
            # Get the actual node at the selected index
            if 0 <= self.selected_index < len(self.file_tree.nodes):
                node = self.file_tree.nodes[self.selected_index]
                node.toggle_selection()
                selected_node = node  # Remember the selected node
                self.selected_index = self.file_tree.update_visible_nodes(selected_node)
                needs_redraw = True
        elif key == curses.KEY_ENTER or key == ord('\n'):
            # Get the actual node at the selected index
            if 0 <= self.selected_index < len(self.file_tree.nodes):
                node = self.file_tree.nodes[self.selected_index]
                if node.is_dir:
                    node.toggle_expansion()
                    selected_node = node  # Remember the selected node
                    self.selected_index = self.file_tree.update_visible_nodes(selected_node)
                    needs_redraw = True
        elif key == ord('a') or key == ord('A'):
            self.file_tree.select_all()
            self.selected_index = 0  # Reset to top
            needs_redraw = True
        elif key == ord('d') or key == ord('D'):
            self.file_tree.deselect_all()
            self.selected_index = 0  # Reset to top
            needs_redraw = True
        elif key == ord('s') or key == ord('S'):
            # Toggle show all files option
            self.file_tree.show_all_files = not self.file_tree.show_all_files
            self.show_all_files = self.file_tree.show_all_files
            selected_node = self.file_tree.nodes[self.selected_index] if self.selected_index < len(self.file_tree.nodes) else None
            self.selected_index = self.file_tree.update_visible_nodes(selected_node)
            needs_redraw = True
        elif key == ord('p') or key == ord('P'):
            # Toggle condensed Python option
            self.condensed_python = not self.condensed_python
            needs_redraw = True
        elif key == ord('q') or key == ord('Q'):
            self.running = False
            self.should_generate = True
        elif key == 27:  # ESC
            self.running = False
            self.should_generate = False
        
        # Set the redraw flag if needed
        if needs_redraw:
            self.needs_redraw = True
            
def extract_python_structure(content: str) -> str:
    """Extract class and function definitions from Python code."""
    try:
        tree = ast.parse(content)
        lines = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get the line number of the class definition
                lines.append(f"class {node.name}:")
                # Add docstring if present
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    docstring = node.body[0].value.value
                    if '\n' in docstring:
                        # Multiline docstring - just take the first line
                        lines.append(f'    """{docstring.splitlines()[0]}..."""')
                    else:
                        lines.append(f'    """{docstring}"""')
                lines.append("")
                
                # Add methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [arg.arg for arg in item.args.args]
                        lines.append(f"    def {item.name}({', '.join(args)}):")
                        if item.returns:
                            lines.append(f"        -> {ast.unparse(item.returns)}")
                        lines.append("")
            
            elif isinstance(node, ast.FunctionDef) and not hasattr(node, 'parent_class'):
                # Top-level function
                args = [arg.arg for arg in node.args.args]
                lines.append(f"def {node.name}({', '.join(args)}):")
                if node.returns:
                    lines.append(f"    -> {ast.unparse(node.returns)}")
                lines.append("")
        
        return "\n".join(lines)
    except:
        # If parsing fails, return a simple placeholder
        return "# Error parsing Python file structure"


def generate_folder_structure(base_path: Path, selected_files: List[Path], show_all_files: bool) -> str:
    """Generate a tree-like folder structure overview."""
    lines = ["# Folder Structure Overview", "", "```"]
    
    # Create a set of selected files for quick lookup
    selected_set = set(selected_files)
    
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
                # Check if this directory has any selected files or if we're showing all files
                has_selected = any(f.is_relative_to(item) for f in selected_set)
                
                # Only show directory if it has selected files OR if show_all_files is True
                if has_selected or show_all_files:
                    lines.append(f"{prefix}{connector}{item.name}/")
                    extension_prefix = "    " if is_last_item else "│   "
                    # Recursively walk subdirectories
                    walk_dir(item, prefix + extension_prefix, is_last_item)
            else:
                # Always show selected files, or all files if show_all_files is enabled
                if item in selected_set or show_all_files:
                    lines.append(f"{prefix}{connector}{item.name}")
    
    # Start from base path
    lines.append(base_path.name + "/")
    walk_dir(base_path, "", True)
    
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)

def collect_files_by_type(selected_files: List[Path]) -> dict:
    """
    Collect selected files organized by type.
    Returns dict with keys: 'markdown', 'text', 'python', 'other'
    """
    files = {
        'markdown': [],
        'text': [],
        'python': [],
        'other': []
    }
    
    for path in selected_files:
        suffix = path.suffix.lower()
        display_name = str(path.relative_to(path.parent.parent))
        
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


def read_file(path: Path, condensed: bool = False) -> str:
    """Read file contents as string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # If this is a Python file and condensed mode is enabled, extract structure
            if condensed and path.suffix.lower() == '.py':
                return extract_python_structure(content)
            
            return content
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
                
                # If this is a Python file and condensed mode is enabled, extract structure
                if condensed and path.suffix.lower() == '.py':
                    return extract_python_structure(content)
                
                return content
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


def generate_file_section(files: list[tuple[str, Path]], section_title: str, condensed: bool = False) -> str:
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
        content = read_file(file_path, condensed)
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


def generate_condensed_python_section(python_files: List[Path], selected_files: List[Path]) -> str:
    """Generate a section for condensed Python files that aren't selected."""
    # Filter out selected Python files
    unselected_python = [f for f in python_files if f not in selected_files]
    
    if not unselected_python:
        return ""
    
    lines = [
        "## Condensed Python Files (Not Selected)",
        "",
        f"> {len(unselected_python)} files",
        ""
    ]
    
    for file_path in sorted(unselected_python, key=lambda x: x.name.lower()):
        display_name = str(file_path.relative_to(file_path.parent.parent))
        content = read_file(file_path, condensed=True)
        
        lines.extend([
            f"### `{display_name}`",
            "",
            "```python",
            content.rstrip(),  # Remove trailing whitespace
            "```",
            "",
            "---",
            ""
        ])
    
    return "\n".join(lines)


def generate_markdown(base_path: Path, selected_files: List[Path], all_python_files: List[Path], 
                     title: str = "Solution Codebase", show_all_files: bool = False, 
                     condensed_python: bool = False) -> str:
    """Generate complete markdown document from selected files."""
    md_lines = [
        f"# {title}",
        "",
        f"> Generated from solution at: `{base_path}`",
        "",
        f"> Options: Show All Files: {'ON' if show_all_files else 'OFF'} | Condensed Python: {'ON' if condensed_python else 'OFF'}",
        "",
        "---",
        "",
    ]
    
    # 1. Folder structure overview
    md_lines.append(generate_folder_structure(base_path, selected_files, show_all_files))
    md_lines.append("---")
    md_lines.append("")
    
    # 2. Organize files by type
    files = collect_files_by_type(selected_files)
    
    # 3. Markdown and text files
    text_files = files['markdown'] + files['text']
    if text_files:
        md_lines.append(generate_file_section(text_files, "Markdown & Text Files"))
    
    # 4. Python files (always show full code for selected files)
    if files['python']:
        md_lines.append(generate_file_section(files['python'], "Python Files", condensed=False))
    
    # 5. Other files
    if files['other']:
        md_lines.append(generate_file_section(files['other'], "Other Files"))
    
    # 6. Condensed Python files (if enabled, for UNSELECTED files)
    if condensed_python:
        md_lines.append(generate_condensed_python_section(all_python_files, selected_files))
    
    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Interactive file selector for combining files into markdown"
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
    parser.add_argument(
        "--show-all-files",
        action="store_true",
        default=True,
        help="Show all files in the folder structure (not just selected ones)"
    )
    parser.add_argument(
        "--condensed-python",
        action="store_true",
        default=True,
        help="Export unselected Python files in condensed form (class/function headers only)"
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
    
    # Run the file selector
    app = FileSelectorApp(base_path)
    app.show_all_files = args.show_all_files
    app.condensed_python = args.condensed_python
    app.file_tree.show_all_files = args.show_all_files
    app.run()
    
    # Check if user wants to generate markdown
    if app.should_generate:
        selected_files = app.file_tree.get_selected_files()
        all_python_files = app.file_tree.get_all_python_files()
        
        if not selected_files:
            print("No files selected. Exiting.")
            return 1
        
        print(f"\nSelected {len(selected_files)} files:")
        for path in sorted(selected_files):
            print(f"  - {path.relative_to(base_path)}")
        
        # Generate markdown
        markdown = generate_markdown(
            base_path, 
            selected_files, 
            all_python_files,
            args.title, 
            app.show_all_files, 
            app.condensed_python
        )
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"\n✓ Created: {output_path}")
        print(f"  Size: {len(markdown):,} characters")
    else:
        print("Operation cancelled.")
    
    return 0


if __name__ == "__main__":
    exit(main())