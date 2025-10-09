```markdown
# Luna Wallet & Node
![Luna Logo]('./node_icon.ico')
![Luna Logo]('./wallet_icon.ico')

A secure, decentralized cryptocurrency wallet and node implementation built with PySide6.

## Features

### Luna Wallet
- **Secure Key Management** - Encrypted private key storage
- **Multi-Currency Support** - Bitcoin, Ethereum, and custom tokens
- **Transaction History** - Complete audit trail of all transactions
- **QR Code Support** - Easy address sharing and payment requests
- **Hardware Wallet Integration** - Ledger and Trezor support
- **Cross-Platform** - Windows, macOS, Linux, and Android support

### Luna Node
- **Full Node Implementation** - Complete blockchain validation
- **Lightning Network** - Fast, low-cost transactions
- **RPC API** - JSON-RPC interface for developers
- **Privacy Focused** - Tor integration and coin control
- **Resource Efficient** - Low memory and CPU footprint
- **Plugin System** - Extensible architecture

## Quick Start

### Prerequisites
- Python 3.9 or higher
- PySide6
- cryptography

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/luna-wallet
cd luna-wallet

# Install dependencies
pip install -r requirements.txt

# Run the wallet
python src/wallet/main.py

# Or run the node
python src/node/main.py
```

### Docker Installation

```bash
# Using Docker Compose
docker-compose up wallet

# Or run node separately
docker-compose up node
```

## Platforms

| Platform | Wallet | Node |
|----------|--------|------|
| Windows | ✅ | ✅ |
| macOS | ✅ | ✅ |
| Linux | ✅ | ✅ |
| Android | ✅ | ⚠️ Experimental |
| iOS | 🔄 Planned | ❌ |

## Architecture

```
luna-wallet/
├── src/
│   ├── wallet/          # GUI wallet application
│   ├── node/            # Blockchain node implementation
│   ├── core/            # Shared cryptographic libraries
│   └── api/             # RPC and REST interfaces
├── assets/
│   ├── icons/           # Application icons
│   ├── themes/          # UI themes
│   └── translations/    # Internationalization
└── tests/               # Test suites
```

## Configuration

### Wallet Configuration
```ini
[wallet]
network = mainnet
currency = BTC
language = en
theme = dark
```

### Node Configuration
```ini
[node]
network = mainnet
rpc_port = 8332
rpc_user = luna
rpc_password = your_password
autostart = true
```

## Development

### Building from Source

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Build executable
pyinstaller build/wallet.spec
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- Private keys never leave the device
- All sensitive data is encrypted at rest
- Regular security audits
- Bug bounty program available

## Support

- **Documentation**: [docs.lunawallet.com](https://docs.lunawallet.com)
- **Community Forum**: [community.lunawallet.com](https://community.lunawallet.com)
- **Issue Tracker**: [GitHub Issues](https://github.com/your-org/luna-wallet/issues)
- **Security Issues**: security@lunawallet.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with PySide6 for cross-platform compatibility
- Uses cryptography libraries from the Python ecosystem
- Inspired by modern wallet design principles
```




