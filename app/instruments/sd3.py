"""Short Dark Triad (SD3), Jones & Paulhus (2014). 27 items, 3 traits."""
from ..core.latin_square import Item
from .likert import LikertInstrument

# (n, text, block, reverse)
_RAW = [
    (1, "It's not wise to tell your secrets.", "Machiavellianism", False),
    (2, "I like to use clever manipulation to get my way.", "Machiavellianism", False),
    (3, "Whatever it takes, you must get the important people on your side.", "Machiavellianism", False),
    (4, "Avoid direct conflict with others because they may be useful in the future.", "Machiavellianism", False),
    (5, "It's wise to keep track of information that you can use against people later.", "Machiavellianism", False),
    (6, "You should wait for the right time to get back at people.", "Machiavellianism", False),
    (7, "There are things you should hide from other people to preserve your reputation.", "Machiavellianism", False),
    (8, "Make sure your plans benefit yourself, not others.", "Machiavellianism", False),
    (9, "Most people can be manipulated.", "Machiavellianism", False),

    (1, "People see me as a natural leader.", "Narcissism", False),
    (2, "I hate being the center of attention.", "Narcissism", True),
    (3, "Many group activities tend to be dull without me.", "Narcissism", False),
    (4, "I know that I am special because everyone keeps telling me so.", "Narcissism", False),
    (5, "I like to get acquainted with important people.", "Narcissism", False),
    (6, "I feel embarrassed if someone compliments me.", "Narcissism", True),
    (7, "I have been compared to famous people.", "Narcissism", False),
    (8, "I am an average person.", "Narcissism", True),
    (9, "I insist on getting the respect I deserve.", "Narcissism", False),

    (1, "I like to get revenge on authorities.", "Psychopathy", False),
    (2, "I avoid dangerous situations.", "Psychopathy", True),
    (3, "Payback needs to be quick and nasty.", "Psychopathy", False),
    (4, "People often say I'm out of control.", "Psychopathy", False),
    (5, "It's true that I can be mean to others.", "Psychopathy", False),
    (6, "People who mess with me always regret it.", "Psychopathy", False),
    (7, "I have never gotten into trouble with the law.", "Psychopathy", True),
    (8, "I enjoy having sex with people I hardly know.", "Psychopathy", False),
    (9, "I'll say anything to get what I want.", "Psychopathy", False),
]

_ITEMS = [
    Item(item_id=f"sd3_{block[:4].lower()}{n}", text=text, block=block, reverse=rev)
    for n, text, block, rev in _RAW
]

_BLOCKS = ["Machiavellianism", "Narcissism", "Psychopathy"]

_ANCHORS = {
    1: "Disagree strongly",
    2: "Disagree",
    3: "Neither agree nor disagree",
    4: "Agree",
    5: "Agree strongly",
}

_INSTRUCTIONS = (
    "You will be shown a numbered list of statements. For each one, indicate how "
    "much you agree with it, using your own judgement -- there are no right or "
    "wrong answers."
)


class SD3Instrument(LikertInstrument):
    def __init__(self):
        super().__init__(
            name="Short Dark Triad (SD3)",
            items=_ITEMS,
            blocks=_BLOCKS,
            scale_min=1,
            scale_max=5,
            scale_anchors=_ANCHORS,
            instructions=_INSTRUCTIONS,
        )
