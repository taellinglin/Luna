from kivy.properties import StringProperty, OptionProperty

from carbonkivy.uix.focuscontainer import FocusContainer


class TransactionTile(FocusContainer):

    amount = StringProperty()

    address = StringProperty()

    status = StringProperty()

    type = OptionProperty("pending", options = ["recieved", "pending", "sent"])

    def __init__(self, *args, **kwargs) -> None:
        super(TransactionTile, self).__init__(*args, **kwargs)
