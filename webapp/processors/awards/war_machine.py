
from processors.awards import AwardProcessor,Column
from models import model_mgr
from models.kits import ASSAULT

class Processor(AwardProcessor):
    '''
    Overview
    This processor keeps track of the most number of kills as assault class

    Implementation
	Cache kill events involving assaulters.
    Notes
	None.
    '''

    def __init__(self):
        AwardProcessor.__init__(self, 'War Machine', 'Most Kills as Assault', [
                Column('Players'), Column('Kills', Column.NUMBER, Column.DESC)])

    def on_kill(self, e):

        # Ignore suicides and team kills
        if not e.valid_kill:
            return

        attacker_kit = model_mgr.get_kit(e.attacker.kit_id)
        if attacker_kit.kit_type == ASSAULT:
            self.results[e.attacker] += 1