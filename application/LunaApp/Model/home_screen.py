from kivy.properties import StringProperty

from Model.base_model import BaseScreenModel


class HomeScreenModel(BaseScreenModel):
    """
    View-Model for HomeScreen.
    """

    wallet_balance = StringProperty("228799.77")

    wallet_address = StringProperty("LUN_9cc3cd8ffff07s56ds_8b7176f5feś")
