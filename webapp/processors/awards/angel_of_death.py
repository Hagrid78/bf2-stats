﻿
from processors.awards import AwardProcessor,Column

class Processor(AwardProcessor):
    '''
    Overview
    This processor keeps track of the number of kills a player gets while they are technically dead.
    This situation can occur primarily with explosive or projectile weapons, such as when someone
    throws a grenade or fires a bazooka, gets killed, and then has their original attack kill
    another player.

    Implementation
    This implementation is based on a simple toggle system. Whenever a kill event is received, the
    victim is enabled to receive an award point in the future and the attacker receives an award
    point if they are currently enabled. When a player subsequently respawns, we disable them from
    receiving award points.

    Pitfalls
    Make sure a player is disabled for any other cases that would allow them to continue getting
    kills normally, such as being revived by a medic. Kills must occur at a later game tick time to
    count towards this award to avoid counting the more common case of simultaneous kills.
    '''

    def __init__(self):
        AwardProcessor.__init__(self, 'Angel of Death', 'Most Kills After Death', [
                Column('Players'), Column('Kills', Column.NUMBER, Column.DESC)])

        # Keep track of all the players currently killed
        self.killed = dict()

    def on_kill(self, e):

        # Enable this award for a player upon being killed
        self.killed[e.victim] = e

        # Check whether the attacker is currently killed
        if e.attacker in self.killed:

            # Make sure the kill was not simultaneous
            old_event = self.killed[e.attacker]
            if (e.tick > old_event.tick):
                self.results[e.attacker] += 1

    def on_revive(self, e):

        # Disable this award for a player when revived
        if e.receiver in self.killed:
            del self.killed[e.receiver]

    def on_spawn(self, e):

        # Disable this award for a player when spawned
        if e.player in self.killed:
            del self.killed[e.player]