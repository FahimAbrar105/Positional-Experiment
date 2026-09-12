"""Moral Foundations Questionnaire (MFQ-30), Graham, Haidt & Nosek.
30 scored items (of 32 numbered; 2 foils excluded) across 5 foundations.

Part 1 items ("relevance", noun-phrase stems) and Part 2 items ("judgment",
full-sentence statements) share the same 0-5 numeric range but different
anchor wording, so each item's kind is tagged inline in its displayed text --
this keeps every condition (including full item shuffle) unambiguous.
"""
from ..core.latin_square import Item
from .likert import LikertInstrument

# (n, text, block, kind)
_RAW = [
    (1, "Whether or not someone suffered emotionally", "Harm/Care", "relevance"),
    (7, "Whether or not someone cared for someone weak or vulnerable", "Harm/Care", "relevance"),
    (12, "Whether or not someone was cruel", "Harm/Care", "relevance"),
    (17, "Compassion for those who are suffering is the most crucial virtue.", "Harm/Care", "judgment"),
    (23, "One of the worst things a person could do is hurt a defenseless animal.", "Harm/Care", "judgment"),
    (28, "It can never be right to kill a human being.", "Harm/Care", "judgment"),

    (2, "Whether or not some people were treated differently than others", "Fairness/Reciprocity", "relevance"),
    (8, "Whether or not someone acted unfairly", "Fairness/Reciprocity", "relevance"),
    (13, "Whether or not someone was denied his or her rights", "Fairness/Reciprocity", "relevance"),
    (18, "When the government makes laws, the number one principle should be ensuring that everyone is treated fairly.", "Fairness/Reciprocity", "judgment"),
    (24, "Justice is the most important requirement for a society.", "Fairness/Reciprocity", "judgment"),
    (29, "I think it's morally wrong that rich children inherit a lot of money while poor children inherit nothing.", "Fairness/Reciprocity", "judgment"),

    (3, "Whether or not someone's action showed love for his or her country", "Ingroup/Loyalty", "relevance"),
    (9, "Whether or not someone did something to betray his or her group", "Ingroup/Loyalty", "relevance"),
    (14, "Whether or not someone showed a lack of loyalty", "Ingroup/Loyalty", "relevance"),
    (19, "I am proud of my country's history.", "Ingroup/Loyalty", "judgment"),
    (25, "People should be loyal to their family members, even when they have done something wrong.", "Ingroup/Loyalty", "judgment"),
    (30, "It is more important to be a team player than to express oneself.", "Ingroup/Loyalty", "judgment"),

    (4, "Whether or not someone showed a lack of respect for authority", "Authority/Respect", "relevance"),
    (10, "Whether or not someone conformed to the traditions of society", "Authority/Respect", "relevance"),
    (15, "Whether or not an action caused chaos or disorder", "Authority/Respect", "relevance"),
    (20, "Respect for authority is something all children need to learn.", "Authority/Respect", "judgment"),
    (26, "Men and women each have different roles to play in society.", "Authority/Respect", "judgment"),
    (31, "If I were a soldier and disagreed with my commanding officer's orders, I would obey anyway because that is my duty.", "Authority/Respect", "judgment"),

    (5, "Whether or not someone violated standards of purity and decency", "Purity/Sanctity", "relevance"),
    (11, "Whether or not someone did something disgusting", "Purity/Sanctity", "relevance"),
    (16, "Whether or not someone acted in a way that God would approve of", "Purity/Sanctity", "relevance"),
    (21, "People should not do things that are disgusting, even if no one is harmed.", "Purity/Sanctity", "judgment"),
    (27, "I would call some acts wrong on the grounds that they are unnatural.", "Purity/Sanctity", "judgment"),
    (32, "Chastity is an important and valuable virtue.", "Purity/Sanctity", "judgment"),
]

_KIND_TAG = {"relevance": "[Moral relevance]", "judgment": "[Agreement]"}

_ITEMS = [
    Item(item_id=f"mfq{n}", text=f"{_KIND_TAG[kind]} {text}", block=block, reverse=False)
    for n, text, block, kind in _RAW
]

_BLOCKS = ["Harm/Care", "Fairness/Reciprocity", "Ingroup/Loyalty", "Authority/Respect", "Purity/Sanctity"]

_INSTRUCTIONS = (
    "You will be shown a numbered list of items about moral judgement. Each item "
    "is tagged with its kind:\n"
    "[Moral relevance] items ask: when you decide whether something is right or "
    "wrong, how relevant is this consideration to your thinking? "
    "(0 = not at all relevant, 5 = extremely relevant)\n"
    "[Agreement] items are statements: how much do you agree with them? "
    "(0 = strongly disagree, 5 = strongly agree)\n"
    "Use your own judgement -- there are no right or wrong answers."
)

_ANCHORS = {
    0: "not at all relevant / strongly disagree",
    1: "not very relevant / disagree",
    2: "slightly relevant / slightly disagree",
    3: "somewhat relevant / slightly agree",
    4: "very relevant / agree",
    5: "extremely relevant / strongly agree",
}


class MFQ30Instrument(LikertInstrument):
    def __init__(self):
        super().__init__(
            name="Moral Foundations Questionnaire (MFQ-30)",
            items=_ITEMS,
            blocks=_BLOCKS,
            scale_min=0,
            scale_max=5,
            scale_anchors=_ANCHORS,
            instructions=_INSTRUCTIONS,
        )
