<p align="center">
<img src= "https://fonts.gstatic.com/s/e/notoemoji/latest/1f4b8/512.webp" , width = "100">
</p>

# Luna Wallet & Node

<p>A PySide6-based cryptocurrency wallet and node implementation.<img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f601/512.webp", width="20"></p>

## Features

### Luna Wallet
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.webp", width = "20">GUI cryptocurrency wallet built with PySide6 </p>
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.webp", width = "20">Basic transaction functionality</p>
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.webp", width = "20">Cross-platform support (Windows, Linux, macOS)</p>

### Luna Node
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.webp", width = "20">Blockchain node implementation</p>
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.webp", width = "20">Peer-to-peer networking</p>
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.webp", width = "20">Transaction validation</p>

## Requirements

<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/203c_fe0f/512.webp", width = "20">Python 3.8+</p>
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/203c_fe0f/512.webp", width = "20">PySide6</p>
<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/203c_fe0f/512.webp", width = "20">Additional dependencies in `requirements.txt`</p>

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

<p><img src="https://fonts.gstatic.com/s/e/notoemoji/latest/26a0_fe0f/512.webp", width="20">MIT License - see LICENSE file for details.</p>






