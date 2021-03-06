from processors.awards import AwardProcessor,Column,PLAYER_COL
from models.vehicles import AIR
from timer import Timer

class Processor(AwardProcessor):
    '''
    Overview
    This award is given to the player who enters an air vehicle the fastest from spawn.
    '''

    def __init__(self):
        AwardProcessor.__init__(self, 'Wright Brothers',
                'Fastest to an Air Vehicle',
                [PLAYER_COL, Column('Time', Column.NUMBER, Column.ASC)])

        self.spawn_times = dict()

    def on_spawn(self, e):
        self.spawn_times[e.player] = e.tick

    def on_vehicle_enter(self, e):
        if e.vehicle.group == AIR:
            enter_time = e.tick - self.spawn_times[e.player]

            air_timer = Timer()
            air_timer.elapsed = enter_time

            if e.player in self.results:
                self.results[e.player] = min(air_timer, self.results[e.player])
            else:
                self.results[e.player] = air_timer
