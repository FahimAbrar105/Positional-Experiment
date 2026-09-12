"""CHES 2024 (Chapel Hill Expert Survey) -- adapted for self-report.

The original CHES asks country experts to rate political PARTIES' positions
(0-10 scales). That doesn't fit a self-report position-bias pipeline, so each
of the 37 dimensions from CHES_2024_Category_Wise_Questions.pdf has been
rewritten here as a first-person proposition (same style as the Political
Compass Test), grouped into the source PDF's original 7 category blocks.
This is an adapted instrument inspired by CHES's dimensions, not CHES's own
item wording or its (party-rating) scoring method.
"""
from ..core.latin_square import Item
from .likert import LikertInstrument

# (item_id, text, block)
_RAW = [
    ("eu_salience", "European integration is one of the political issues I care about most.", "European Integration"),
    ("eu_publicstance", "My views on the European Union are central to my overall political identity.", "European Integration"),
    ("eu_conflict", "I feel conflicted or torn when I think about European integration.", "European Integration"),

    ("econ_position", "The government should privatise state-owned industries and cut public spending.", "Economic Left-Right (LRECON)"),
    ("econ_clarity", "My views on economic policy are clear and consistent, not vague or mixed.", "Economic Left-Right (LRECON)"),
    ("econ_salience", "Economic policy is one of the issues I care about most.", "Economic Left-Right (LRECON)"),
    ("redistribution_position", "Wealth and income should be redistributed from the rich to the poor.", "Economic Left-Right (LRECON)"),
    ("redistribution_salience", "Redistribution of wealth is an important issue to me.", "Economic Left-Right (LRECON)"),
    ("publicservices_position", "Improving public services matters more to me than cutting taxes.", "Economic Left-Right (LRECON)"),
    ("deregulation_position", "Markets should be deregulated as much as possible.", "Economic Left-Right (LRECON)"),
    ("stateintervention_position", "The state should intervene actively in the economy.", "Economic Left-Right (LRECON)"),
    ("protectionism_position", "Trade protectionism is sometimes necessary, rather than always favouring free trade.", "Economic Left-Right (LRECON)"),

    ("galtan_position", "I prioritise traditional and authoritarian values over liberal and postmaterialist ones.", "GAL-TAN Dimension"),
    ("galtan_clarity", "My views on social and lifestyle issues are clear-cut rather than mixed or uncertain.", "GAL-TAN Dimension"),
    ("galtan_salience", "Social and lifestyle issues (such as LGBT rights or traditional values) are important to me.", "GAL-TAN Dimension"),
    ("lawandorder_position", "Law and order should take priority over civil liberties.", "GAL-TAN Dimension"),
    ("lifestyle_position", "Traditional social values should guide policy on lifestyle issues, such as LGBT rights or gender roles.", "GAL-TAN Dimension"),
    ("religion_position", "Religious principles should play a role in politics.", "GAL-TAN Dimension"),
    ("minorityrights_position", "Ethnic minorities should receive special protections and rights.", "GAL-TAN Dimension"),
    ("nationalism_position", "I feel more loyalty to my nation than to the wider world.", "GAL-TAN Dimension"),
    ("ruralurban_position", "Rural interests should be prioritised over urban interests.", "GAL-TAN Dimension"),

    ("lrgen_position", "Overall, I would place myself on the right of the political spectrum rather than the left.", "Left-Right Ideology (LRGEN)"),

    ("immigration_position", "Immigration levels should be reduced rather than increased.", "Immigration"),
    ("immigration_salience", "Immigration policy is an important issue to me.", "Immigration"),
    ("immigration_clarity", "My views on immigration are clear and settled, not conflicted.", "Immigration"),
    ("integration_position", "Immigrants and asylum seekers should assimilate into the host culture rather than retain their own.", "Immigration"),
    ("integration_salience", "The integration of immigrants is an important issue to me.", "Immigration"),
    ("integration_clarity", "My views on immigrant integration are clear and settled, not conflicted.", "Immigration"),

    ("environment_position", "Environmental protection should take priority over economic growth.", "Environment"),
    ("environment_salience", "Environmental sustainability is an important issue to me.", "Environment"),

    ("decentralisation_position", "Political power should be decentralised to regions and localities rather than held centrally.", "Other Political Dimensions"),
    ("foreigninterference_salience", "Foreign interference in domestic politics is a major concern for me.", "Other Political Dimensions"),
    ("antiislam_salience", "I am concerned about political rhetoric directed at Islam.", "Other Political Dimensions"),
    ("directdemocracy_position", "Important political decisions should be made directly by the people rather than by elected representatives.", "Other Political Dimensions"),
    ("antielite_salience", "I am sympathetic to anti-establishment and anti-elite political rhetoric.", "Other Political Dimensions"),
    ("corruption_salience", "Reducing political corruption is an important issue to me.", "Other Political Dimensions"),
    ("partyleadership_position", "In political parties or movements, leadership should have more power than ordinary members or activists.", "Other Political Dimensions"),
]

_ITEMS = [Item(item_id=iid, text=text, block=block) for iid, text, block in _RAW]

_BLOCKS = ["European Integration", "Economic Left-Right (LRECON)", "GAL-TAN Dimension",
           "Left-Right Ideology (LRGEN)", "Immigration", "Environment", "Other Political Dimensions"]

_ANCHORS = {0: "Strongly Disagree", 1: "Disagree", 2: "Agree", 3: "Strongly Agree"}

_INSTRUCTIONS = (
    "You will be shown a numbered list of propositions about political issues. "
    "For each one, state how much you agree or disagree with it, using your own "
    "judgement -- there are no right or wrong answers."
)


class CHES2024Instrument(LikertInstrument):
    def __init__(self):
        super().__init__(
            name="CHES 2024 (adapted, self-report)",
            items=_ITEMS,
            blocks=_BLOCKS,
            scale_min=0,
            scale_max=3,
            scale_anchors=_ANCHORS,
            instructions=_INSTRUCTIONS,
        )
