
from events import FlagActionEvent
from processors.awards import AwardProcessor,Column,PLAYER_COL
from stats import stat_mgr

class Processor(AwardProcessor):
    '''
    Overview
    This processor is awarded to the player with the most flag neutralize assists.

    Implementation
    Count the flag action events of the appropriate type.

    Notes
    None.
    '''

    def __init__(self):
        AwardProcessor.__init__(self, 'Wingman', 'Most Flag Neutralize Assists',
                [PLAYER_COL, Column('Neutralize Assists', Column.NUMBER, Column.DESC)])

    def on_flag_action(self, e):
        if e.action_type == FlagActionEvent.NEUTRALIZE_ASSIST:
            self.results[e.player] += 1
