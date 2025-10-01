from View.HomeScreen.home_screen import HomeScreenView
from View.AboutScreen.about_screen import AboutScreenView

from Model.home_screen import HomeScreenModel
from Model.about_screen import AboutScreenModel

screens = {
    'home screen': {
        'object': HomeScreenView,
        'module': 'View.HomeScreen',
        'model': HomeScreenModel,
    },
    'about screen': {
        'object': AboutScreenView,
        'module': 'View.AboutScreen',
        'model': AboutScreenModel,
    },
}
