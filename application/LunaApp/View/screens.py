from View.HomeScreen.home_screen import HomeScreenView
from View.AuthScreen.auth_screen import AuthScreenView

from Model.home_screen import HomeScreenModel
from Model.auth_screen import AuthScreenModel

screens = {
    'home': {
        'object': HomeScreenView,
        'model': HomeScreenModel,
        'module': 'View.HomeScreen'
    },
    'auth screen': {
        'object': AuthScreenView,
        'model': AuthScreenModel,
        'module': 'View.AuthScreen'
    },
}