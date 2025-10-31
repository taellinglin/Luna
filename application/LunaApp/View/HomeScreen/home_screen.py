from kivy.properties import StringProperty

from View.base_screen import BaseScreenView


class HomeScreenView(BaseScreenView):

    wallet_balance = StringProperty("228799.77")

    wallet_address = StringProperty("LUN_9cc3cd8ffff07s56ds_8b7176f5fe")

    def __init__(self, **kwargs) -> None:
        super(HomeScreenView, self).__init__(**kwargs)
