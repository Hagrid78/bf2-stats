from processors.awards import AwardProcessor,Column
from stats import stat_mgr

class Processor(AwardProcessor):
    '''
    Overview
    This award is given to the player with the most kills against lower ranked players.
    '''

    def __init__(self):
        AwardProcessor.__init__(self, 'Bully',
                'Most Kills Against Lower Ranked Players', [
                Column('Players'), Column('Kills', Column.NUMBER, Column.DESC)])

    def on_kill(self, e):
        attacker_stats = stat_mgr.get_player_stats(e.attacker)
        victim_stats = stat_mgr.get_player_stats(e.victim)

        if attacker_stats.rank >= 3 and victim_stats.rank <= 1:
            self.results[e.attacker] += 1