__app_name__ = "Luna"
__version__ = "0.0.1"

from kivy.logger import Logger

import design.factory_registers
from design.config import ROOT

Logger.info(f"{__app_name__}: {__version__}")
Logger.info(f"{__app_name__}: Installed at {ROOT}")
