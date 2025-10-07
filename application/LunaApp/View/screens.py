# View/screens.py
from Model.setup_screen import SetupScreenModel
from Model.password_screen import PasswordScreenModel
from Model.balance_screen import BalanceScreenModel
from Model.send_receive_screen import SendReceiveScreenModel
from Model.history_screen import HistoryScreenModel

from Controller.setup_screen import SetupScreenController
from Controller.password_screen import PasswordScreenController
from Controller.balance_screen import BalanceScreenController
from Controller.send_receive_screen import SendReceiveScreenController
from Controller.history_screen import HistoryScreenController

from View.SetupScreen.setup_screen import SetupScreenView
from View.PasswordScreen.password_screen import PasswordScreenView
from View.BalanceScreen.balance_screen import BalanceScreenView
from View.SendReceiveScreen.send_receive_screen import SendReceiveScreenView
from View.HistoryScreen.history_screen import HistoryScreenView

screens = {
    "setup": {
        "model": SetupScreenModel,
        "controller": SetupScreenController,
        "view": SetupScreenView,
    },
    "password": {
        "model": PasswordScreenModel,
        "controller": PasswordScreenController,
        "view": PasswordScreenView,
    },
    "balance": {
        "model": BalanceScreenModel,
        "controller": BalanceScreenController,
        "view": BalanceScreenView,
    },
    "send_receive": {
        "model": SendReceiveScreenModel,
        "controller": SendReceiveScreenController,
        "view": SendReceiveScreenView,
    },
    "history": {
        "model": HistoryScreenModel,
        "controller": HistoryScreenController,
        "view": HistoryScreenView,
    },
}