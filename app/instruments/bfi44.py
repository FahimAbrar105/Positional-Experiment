"""Big Five Inventory (BFI-44), John & Srivastava (1999). 44 items, 5 traits.

Item text/keying taken from BFI44_Category_Wise_Questions_With_Items.pdf.
Each item completes the stem "I see myself as someone who ...".
"""
from ..core.latin_square import Item
from .likert import LikertInstrument

# (n, phrase, block, reverse)
_RAW = [
    (1, "is talkative", "Extraversion", False),
    (6, "is reserved", "Extraversion", True),
    (11, "is full of energy", "Extraversion", False),
    (16, "generates a lot of enthusiasm", "Extraversion", False),
    (21, "tends to be quiet", "Extraversion", True),
    (26, "has an assertive personality", "Extraversion", False),
    (31, "is sometimes shy, inhibited", "Extraversion", True),
    (36, "is outgoing, sociable", "Extraversion", False),

    (2, "tends to find fault with others", "Agreeableness", True),
    (7, "is helpful and unselfish with others", "Agreeableness", False),
    (12, "starts quarrels with others", "Agreeableness", True),
    (17, "has a forgiving nature", "Agreeableness", False),
    (22, "is generally trusting", "Agreeableness", False),
    (27, "can be cold and aloof", "Agreeableness", True),
    (32, "is considerate, kind to almost everyone", "Agreeableness", False),
    (37, "is sometimes rude to others", "Agreeableness", True),
    (42, "likes to cooperate with others", "Agreeableness", False),

    (3, "does a thorough job", "Conscientiousness", False),
    (8, "can be somewhat careless", "Conscientiousness", True),
    (13, "is a reliable worker", "Conscientiousness", False),
    (18, "tends to be disorganized", "Conscientiousness", True),
    (23, "tends to be lazy", "Conscientiousness", True),
    (28, "perseveres until the task is finished", "Conscientiousness", False),
    (33, "does things efficiently", "Conscientiousness", False),
    (38, "makes plans and follows through on them", "Conscientiousness", False),
    (43, "is easily distracted", "Conscientiousness", True),

    (4, "is depressed, blue", "Neuroticism", False),
    (9, "is relaxed, handles stress well", "Neuroticism", True),
    (14, "can be tense", "Neuroticism", False),
    (19, "worries a lot", "Neuroticism", False),
    (24, "is emotionally stable, not easily upset", "Neuroticism", True),
    (29, "can be moody", "Neuroticism", False),
    (34, "remains calm in tense situations", "Neuroticism", True),
    (39, "gets nervous easily", "Neuroticism", False),

    (5, "is original, comes up with new ideas", "Openness", False),
    (10, "is curious about many different things", "Openness", False),
    (15, "is ingenious, a deep thinker", "Openness", False),
    (20, "has an active imagination", "Openness", False),
    (25, "is inventive", "Openness", False),
    (30, "values artistic, aesthetic experiences", "Openness", False),
    (35, "prefers work that is routine", "Openness", True),
    (40, "likes to reflect, play with ideas", "Openness", False),
    (41, "has few artistic interests", "Openness", True),
    (44, "is sophisticated in art, music, or literature", "Openness", False),
]

_ITEMS = [
    Item(item_id=f"bfi{n}", text=f"I see myself as someone who {phrase}.", block=block, reverse=rev)
    for n, phrase, block, rev in _RAW
]

_BLOCKS = ["Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]

_ANCHORS = {
    1: "Disagree strongly",
    2: "Disagree a little",
    3: "Neither agree nor disagree",
    4: "Agree a little",
    5: "Agree strongly",
}

_INSTRUCTIONS = (
    "You will be shown a numbered list of statements, each describing a possible "
    "personal trait. For each one, indicate how much you agree that the statement "
    "describes you, using your own judgement -- there are no right or wrong answers."
)


class BFI44Instrument(LikertInstrument):
    def __init__(self):
        super().__init__(
            name="Big Five Inventory (BFI-44)",
            items=_ITEMS,
            blocks=_BLOCKS,
            scale_min=1,
            scale_max=5,
            scale_anchors=_ANCHORS,
            instructions=_INSTRUCTIONS,
        )
