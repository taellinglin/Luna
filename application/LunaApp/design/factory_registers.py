import os

from kivy.core.text import LabelBase
from kivy.factory import Factory

from design.config import DATA

# Alias for the register function from Factory
register = Factory.register

"""
Registers custom components to the Kivy Factory.

This code registers each component within the "uix" directory to the Kivy Factory. 
Once registered, the components can be used without explicitly importing them elsewhere in the kvlang files.
"""
register("LScreen", module="design.uix.screen")
register("LBoxLayout", module="design.uix.boxlayout")
register("LStackLayout", module="design.uix.stacklayout")
register("LAnchorLayout", module="design.uix.anchorlayout")
register("LButton", module="design.uix.button")
register("LButtonIcon", module="design.uix.button")
register("LButtonLabel", module="design.uix.button")
register("LButtonPrimary", module="design.uix.button")
register("LButtonSecondary", module="design.uix.button")
register("LButtonTertiary", module="design.uix.button")
register("LButtonDanger", module="design.uix.button")
register("LButtonGhost", module="design.uix.button")
register("LGridLayout", module="design.uix.gridlayout")
register("LDivider", module="design.uix.divider")
register("LScrollView", module="design.uix.scrollview")
register("LIcon", module="design.uix.icon")
register("LLabel", module="design.uix.label")
register("LIconCircular", module="design.uix.icon")
register("LBaseIcon", module="design.uix.icon")


# Register the behavior with Kivy's Factory
register("AdaptiveBehavior", module="design.behaviors.adaptive_behavior")
register(
    "BackgroundColorBehaviorCircular", module="design.behaviors.background_color_behavior"
)
register(
    "BackgroundColorBehaviorRectangular",
    module="design.behaviors.background_color_behavior",
)
register("ElevationBehavior", module="design.behaviors.elevation_behavior")
register("HierarchicalLayerBehavior", module="design.behaviors.hierarchical_layer_behavior")
register("HoverBehavior", module="design.behaviors.hover_behavior")
register("StateFocusBehavior", module="design.behaviors.state_focus_behavior")


# Alias for the register function from Factory
font_register = LabelBase.register

"""
Registers custom fonts to the Kivy LabelBase.

Once registered, the fonts can be used without explicitly importing them elsewhere in the kvlang files.
"""

# Register the font with the LabelBase
font_register("cicon", os.path.join(DATA, "Icons", "carbondesignicons.ttf"))

ibmplexsansregular = os.path.join(
    DATA, "IBMPlex", "IBM_Plex_Sans", "static", "IBMPlexSans-Regular.ttf"
)
ibmplexsansbold = os.path.join(
    DATA, "IBMPlex", "IBM_Plex_Sans", "static", "IBMPlexSans-Bold.ttf"
)
ibmplexsansitalic = os.path.join(
    DATA, "IBMPlex", "IBM_Plex_Sans", "static", "IBMPlexSans-Italic.ttf"
)
ibmplexsansbolditalic = os.path.join(
    DATA, "IBMPlex", "IBM_Plex_Sans", "static", "IBMPlexSans-BoldItalic.ttf"
)

font_register(
    "ibmplexsans",
    fn_regular=ibmplexsansregular,
    fn_bold=ibmplexsansbold,
    fn_italic=ibmplexsansitalic,
    fn_bolditalic=ibmplexsansbolditalic,
)
