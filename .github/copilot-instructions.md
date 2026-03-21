# AAIA Copilot Instructions

**Main instruction file - See topic-specific files for detailed guidance**

## Quick Reference

For detailed instructions on specific topics, Copilot can reference:
- **Architecture**: `.github/copilot-instructions-architecture.md` - DI Container, PromptManager, Event Bus
- **Testing**: `.github/copilot-instructions-testing.md` - WSL, CLI, batch mode testing
- **Build & Scripts**: `.github/copilot-instructions-build.md` - Python compilation, bash script standards
- **Patterns**: `.github/copilot-instructions-patterns.md` - Code templates, common patterns
- **WIP Workflow**: `.github/copilot-instructions-wip-workflow.md` - WIP.md → decisions → roadmap batches

## Essential Constraints (Always Apply)

- ❌ **NO direct instantiation** - use DI Container
- ❌ **NO hardcoded prompts** - use PromptManager
- ✅ **Always register** new modules in `modules/setup.py`
- ✅ **Bash scripts: LF line endings only** (not CRLF)
- ✅ **Python build: use `py_compile`** for verification
- ⚠️ **Per-implementation phase: create ONLY ONE final markdown summary file**

## Project Context

- **Language**: Python (no traditional build needed)
- **Environment**: WSL + Nix (required for testing)
- **Architecture**: DI Container + Event Bus + PromptManager
- **Path**: `/mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia`

## When to Reference Specific Instructions

- **Adding new module?** → See `copilot-instructions-architecture.md`
- **Running tests?** → See `copilot-instructions-testing.md`
- **Creating bash script?** → See `copilot-instructions-build.md`
- **Need code template?** → See `copilot-instructions-patterns.md`
- **Processing WIP.md items into a roadmap?** → See `copilot-instructions-wip-workflow.md`

