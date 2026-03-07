# AAIA - Autonomous AI Agent

An autonomous AI agent system designed for self-improvement and task execution.

## Quick Start (NixOS)

```bash
git clone https://github.com/matren6/aaia.git
cd aaia
chmod +x install.sh
sudo ./install.sh
```

**For complete deployment instructions, see [SETUP.md](SETUP.md)**

## What is AAIA?

AAIA (Autonomous AI Agent) is a self-evolving AI system that:
- Autonomously manages and executes tasks
- Continuously improves its own capabilities
- Adapts to new environments and challenges
- Maintains economic and strategic optimization

## Features

- 🤖 **Autonomous Operation** - Self-directed task management
- 🧠 **Self-Modification** - Evolves and improves its own code
- 📊 **Economic Management** - Cost-aware decision making
- 🔄 **Continuous Learning** - Learns from experience
- 🏗️ **Tool Creation** - Generates new tools as needed
- 🔍 **Environment Exploration** - Discovers and adapts to new capabilities

## Architecture

AAIA is built on a modular architecture with:
- **Event Bus** - Asynchronous communication between modules
- **Dependency Injection** - Clean component management
- **Goal System** - Hierarchical goal planning and execution
- **Evolution Pipeline** - Continuous self-improvement
- **Metacognition** - Self-awareness and reflection

## Deployment

### NixOS (Recommended)

AAIA is designed to run on NixOS with full Nix integration:

- **Automated Deployment**: One-command installation
- **Reproducible Builds**: Guaranteed consistent environments
- **Systemd Service**: Runs as a managed system service
- **Security Hardened**: Isolated user, resource limits, protected directories

See [SETUP.md](SETUP.md) for complete instructions.

### System Requirements

- NixOS (latest stable or unstable)
- 2GB+ RAM
- 2 CPU cores recommended
- Internet connectivity for initial build

## Project Structure

```
aaia/
├── packages/
│   ├── main.py              # Entry point
│   ├── modules/             # Core modules
│   └── prompts/             # LLM prompts
├── scripts/                 # Build and deployment scripts
├── flake.nix               # Nix flake configuration
├── configuration.nix        # NixOS system configuration
├── install.sh              # Automated installer
├── test-installation.sh    # Installation verification
└── SETUP.md          # Complete deployment guide
```

## Development

Enter the development environment:

```bash
nix develop
```

This provides all dependencies and proper Python environment setup.

## Service Management

```bash
# Check status
systemctl status aaia

# View logs
journalctl -u aaia -f

# Restart service
sudo systemctl restart aaia
```

## Configuration

AAIA configuration is managed through:
- **Environment Variables** in `configuration.nix`
- **Runtime Data** in `/var/lib/aaia/`
- **System Settings** in `packages/modules/settings.py`

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test in a NixOS VM
4. Submit a pull request

## License

[Add your license here]

## Support

- 📖 **Documentation**: [SETUP.md](SETUP.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/matren6/aaia/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/matren6/aaia/discussions)

## Security

AAIA runs with security hardening:
- Dedicated system user (non-root)
- Protected filesystem access
- Resource limits (CPU/Memory)
- Private temporary directories

**Important**: Review the code before running in production environments.

---

**Ready to deploy?** Start with [SETUP.md](SETUP.md)
