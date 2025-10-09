# Luna Wallet & Node

<p align="center">
  <img src="./wallet_icon.ico" alt="Luna Wallet Icon" width="32">
  <img src="./node_icon.ico" alt="Luna Node Icon" width="32">
</p>

A PySide6-based cryptocurrency wallet and node implementation.

## Features

### Luna Wallet
- GUI cryptocurrency wallet built with PySide6
- Basic transaction functionality
- Cross-platform support (Windows, Linux, macOS)

### Luna Node
- Blockchain node implementation
- Peer-to-peer networking
- Transaction validation

## Requirements

- Python 3.8+
- PySide6
- Additional dependencies in `requirements.txt`

## Installation

```bash
git clone https://github.com/taellinglin/Luna
cd Luna
pip install -r requirements.txt
```

## Usage

### Running the Wallet
```bash
python luna_wallet_gui.py
```

### Running the Node
```bash
python luna_node_gui.py
```

## Project Structure

```
Luna/
├── wallet_main.py      # Wallet application entry point
├── node_main.py        # Node application entry point  
├── wallet_icon.ico     # Wallet application icon
├── node_icon.ico       # Node application icon
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Building

The project uses PySide6 for the GUI and can be packaged using PyInstaller:

```bash
pyinstaller --onefile --windowed --icon=wallet_icon.ico LunaWalletGUI.spec
pyinstaller --onefile --windowed --icon=node_icon.ico LunaNodeGUI.spec
or just..
./build_with_installers.bat

```

## Development

This is a personal project for learning cryptocurrency wallet and node development with Python and PySide6.

## License

MIT License - see LICENSE file for details.




