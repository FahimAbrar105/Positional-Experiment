"""Instrument registry -- add new instruments here once their item banks are built."""
from .political_compass import PoliticalCompassInstrument
from .bfi44 import BFI44Instrument
from .sd3 import SD3Instrument
from .mfq30 import MFQ30Instrument
from .mfv import MFVInstrument
from .srpd import SRPDInstrument

INSTRUMENTS = {
    "Political Compass Test": PoliticalCompassInstrument(),
    "Big Five Inventory (BFI-44)": BFI44Instrument(),
    "Short Dark Triad (SD3)": SD3Instrument(),
    "Moral Foundations Questionnaire (MFQ-30)": MFQ30Instrument(),
    "Moral Foundations Vignettes (MFV)": MFVInstrument(),
    "Self-Reported Political Dimensions (SRPD)": SRPDInstrument(),
}
