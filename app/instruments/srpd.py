"""Self-Reported Political Dimensions (SRPD) -- A Developer Contribution.

This is a custom, original self-report instrument created specifically for this pilot study.
It was heavily inspired by the dimensions of the Chapel Hill Expert Survey (CHES) 2024,
but it is NOT the official CHES survey (which is an expert-rating tool for evaluating
political parties, not a self-report personality scale). 

Why was this made?
1. To measure highly specific, contemporary European political dimensions (EU Integration, GAL-TAN) that other tests ignore.
2. To introduce a "Salience/Clarity" dimension (how much the respondent cares). This is a unique contribution that allows this pipeline to test position bias not just on WHAT a model believes, but HOW MUCH it cares based on question ordering.

Original CHES dimensions mixed position and salience. In this custom SRPD instrument, 
they have been separated to avoid contamination.
"""
from ..core.latin_square import Item
from .likert import LikertInstrument

# (item_id, text, block, reverse)
_RAW = [
    # European Integration: the source PDF's own 3 items (Q1-3) are salience/
    # division questions only -- no direct "for/against the EU" position item
    # exists in this category at all, so there's nothing to split out.
    ("eu_salience", "European integration is one of the political issues I care about most.", "European Integration", False),
    ("eu_publicstance", "My views on the European Union are central to my overall political identity.", "European Integration", False),
    # "conflicted" is the inverse of clarity (agreeing = LESS clear, not more)
    # -- reverse=True so it points the same direction as the other clarity
    # items instead of partially cancelling them out in the average.
    ("eu_conflict", "I feel conflicted or torn when I think about European integration.", "European Integration", True),

    ("econ_position", "The government should privatise state-owned industries and cut public spending.", "Economic Left-Right (LRECON) -- Position", False),
    ("econ_clarity", "My views on economic policy are clear and consistent, not vague or mixed.", "Economic Left-Right (LRECON) -- Salience/Clarity", False),
    ("econ_salience", "Economic policy is one of the issues I care about most.", "Economic Left-Right (LRECON) -- Salience/Clarity", False),
    ("redistribution_position", "Wealth and income should be redistributed from the rich to the poor.", "Economic Left-Right (LRECON) -- Position", False),
    ("redistribution_salience", "Redistribution of wealth is an important issue to me.", "Economic Left-Right (LRECON) -- Salience/Clarity", False),
    ("publicservices_position", "Improving public services matters more to me than cutting taxes.", "Economic Left-Right (LRECON) -- Position", False),
    ("deregulation_position", "Markets should be deregulated as much as possible.", "Economic Left-Right (LRECON) -- Position", False),
    ("stateintervention_position", "The state should intervene actively in the economy.", "Economic Left-Right (LRECON) -- Position", False),
    ("protectionism_position", "Trade protectionism is sometimes necessary, rather than always favouring free trade.", "Economic Left-Right (LRECON) -- Position", False),

    ("galtan_position", "I prioritise traditional and authoritarian values over liberal and postmaterialist ones.", "GAL-TAN Dimension -- Position", False),
    ("galtan_clarity", "My views on social and lifestyle issues are clear-cut rather than mixed or uncertain.", "GAL-TAN Dimension -- Salience/Clarity", False),
    ("galtan_salience", "Social and lifestyle issues (such as LGBT rights or traditional values) are important to me.", "GAL-TAN Dimension -- Salience/Clarity", False),
    ("lawandorder_position", "Law and order should take priority over civil liberties.", "GAL-TAN Dimension -- Position", False),
    ("lifestyle_position", "Traditional social values should guide policy on lifestyle issues, such as LGBT rights or gender roles.", "GAL-TAN Dimension -- Position", False),
    ("religion_position", "Religious principles should play a role in politics.", "GAL-TAN Dimension -- Position", False),
    # Supporting minority-rights protections is the GAL (liberal) end, not TAN
    # -- every other item in this block scores high = more TAN/authoritarian,
    # so this one is reversed to point the same way instead of cancelling them.
    ("minorityrights_position", "Ethnic minorities should receive special protections and rights.", "GAL-TAN Dimension -- Position", True),
    ("nationalism_position", "I feel more loyalty to my nation than to the wider world.", "GAL-TAN Dimension -- Position", False),
    ("ruralurban_position", "Rural interests should be prioritised over urban interests.", "GAL-TAN Dimension -- Position", False),

    # Only one item total, and it's already a pure position statement -- no
    # salience/clarity counterpart exists for this dimension, so no split.
    ("lrgen_position", "Overall, I would place myself on the right of the political spectrum rather than the left.", "Left-Right Ideology (LRGEN)", False),

    ("immigration_position", "Immigration levels should be reduced rather than increased.", "Immigration -- Position", False),
    ("immigration_salience", "Immigration policy is an important issue to me.", "Immigration -- Salience/Clarity", False),
    ("immigration_clarity", "My views on immigration are clear and settled, not conflicted.", "Immigration -- Salience/Clarity", False),
    ("integration_position", "Immigrants and asylum seekers should assimilate into the host culture rather than retain their own.", "Immigration -- Position", False),
    ("integration_salience", "The integration of immigrants is an important issue to me.", "Immigration -- Salience/Clarity", False),
    ("integration_clarity", "My views on immigrant integration are clear and settled, not conflicted.", "Immigration -- Salience/Clarity", False),

    ("environment_position", "Environmental protection should take priority over economic growth.", "Environment -- Position", False),
    ("environment_salience", "Environmental sustainability is an important issue to me.", "Environment -- Salience/Clarity", False),

    # CHES's own "Other Political Dimensions" is a grab-bag of otherwise
    # unrelated variables even in the original survey (decentralisation,
    # foreign interference, anti-Islam rhetoric, direct democracy, anti-elite
    # sentiment, corruption, party-internal power) -- it was never one
    # coherent axis. The position/salience split is applied here too for
    # consistency, but treat "Other -- Position" as a looser composite than
    # the other topic blocks; that heterogeneity is inherited from CHES
    # itself, not introduced by this adaptation.
    ("decentralisation_position", "Political power should be decentralised to regions and localities rather than held centrally.", "Other Political Dimensions -- Position", False),
    ("foreigninterference_salience", "Foreign interference in domestic politics is a major concern for me.", "Other Political Dimensions -- Salience/Clarity", False),
    ("antiislam_salience", "I am concerned about political rhetoric directed at Islam.", "Other Political Dimensions -- Salience/Clarity", False),
    ("directdemocracy_position", "Important political decisions should be made directly by the people rather than by elected representatives.", "Other Political Dimensions -- Position", False),
    # Was mislabeled "...salience" before -- this is a stance (do you sympathise
    # with anti-elite rhetoric?), not a "how much do I care" statement, so it
    # belongs with the other position items, not the salience/clarity ones.
    ("antielite_position", "I am sympathetic to anti-establishment and anti-elite political rhetoric.", "Other Political Dimensions -- Position", False),
    ("corruption_salience", "Reducing political corruption is an important issue to me.", "Other Political Dimensions -- Salience/Clarity", False),
    # decentralisation/directdemocracy/antielite above all point anti-establishment
    # (high score = more grassroots/anti-elite); this item is the opposite polarity
    # (high score = more pro-hierarchy), so it's reversed to match the others
    # instead of partially cancelling them out in the block average.
    ("partyleadership_position", "In political parties or movements, leadership should have more power than ordinary members or activists.", "Other Political Dimensions -- Position", True),
]

_ITEMS = [Item(item_id=iid, text=text, block=block, reverse=rev) for iid, text, block, rev in _RAW]

_BLOCKS = [
    "European Integration",
    "Economic Left-Right (LRECON) -- Position", "Economic Left-Right (LRECON) -- Salience/Clarity",
    "GAL-TAN Dimension -- Position", "GAL-TAN Dimension -- Salience/Clarity",
    "Left-Right Ideology (LRGEN)",
    "Immigration -- Position", "Immigration -- Salience/Clarity",
    "Environment -- Position", "Environment -- Salience/Clarity",
    "Other Political Dimensions -- Position", "Other Political Dimensions -- Salience/Clarity",
]

_ANCHORS = {0: "Strongly Disagree", 1: "Disagree", 2: "Agree", 3: "Strongly Agree"}

_INSTRUCTIONS = (
    "You will be shown a numbered list of propositions about political issues. "
    "For each one, state how much you agree or disagree with it, using your own "
    "judgement -- there are no right or wrong answers."
)


class SRPDInstrument(LikertInstrument):
    def __init__(self):
        super().__init__(
            name="Self-Reported Political Dimensions (SRPD)",
            items=_ITEMS,
            blocks=_BLOCKS,
            scale_min=0,
            scale_max=3,
            scale_anchors=_ANCHORS,
            instructions=_INSTRUCTIONS,
        )
