from kivy.properties import StringProperty

from Model.base_model import BaseScreenModel


class AuthScreenModel(BaseScreenModel):
    """
    View-Model for AuthScreen.
    """

    wallet_balance = StringProperty("228799.77")

    wallet_address = StringProperty("LUN_9cc3cd8ffff07s56ds_8b7176f5feś")

    def __init__(self, *args, **kwargs):
        super(AuthScreenModel, self).__init__(*args, **kwargs)
