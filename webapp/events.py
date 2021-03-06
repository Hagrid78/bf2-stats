﻿
import time

import models

from models import model_mgr

class EventHistory(object):

    def __init__(self):

        self.ticked = False # Whether or not the newest event caused the game time to advance
        self.old_tick = 0 # The game time of the older batch of events
        self.new_tick = 0 # The game time of the newest batch of events
        self.old_events = list() # A list of events for the older game time
        self.new_events = list() # A list of events for the newest game time
        self.old_event_types = dict() # A map of event type to event for older events
        self.new_event_types = dict() # A map of event type to event for newest events

    def add_event(self, event):
        '''
        Adds a log event to the history of this statistics model for use by processors.

        Args:
           event (BaseEvent): Object representation of a log entry.

        Returns:
            None
        '''

        if not event: return

        # Update the event history based on game time ticks
        if event.tick > self.new_tick:
            self.old_tick = self.new_tick
            self.old_events = self.new_events

            self.new_tick = event.tick
            del self.new_events[:]
            ticked = True
        else:
            ticked = False
        self.new_events.append(event)

        # Update the event history based on event type
        if event.TYPE in self.new_event_types:
            self.old_event_types[event.TYPE] = self.new_event_types[event.TYPE]
        self.new_event_types[event.TYPE] = event

    def get_old_event(self, event_type):
        '''
        Gets the older/previous registered event that matches the given identifier.

        Args:
           event_type (string): The unique identifier for a type of event.

        Returns:
            event (BaseEvent): An event that occurred at a previous tick.
        '''

        if event_type and event_type in self.old_event_types:
            return self.old_event_types[event_type]
        return None

    def get_new_event(self, event_type):
        '''
        Gets the newest/recent registered event that matches the given identifier.

        Args:
           event_type (string): The unique identifier for a type of event.

        Returns:
            event (BaseEvent): An event that occurred at the most recent tick.
        '''

        if event_type and event_type in self.new_event_types:
            return self.new_event_types[event_type]
        return None

class EventManager(object):

    def __init__(self):
        self.event_types = dict()
        self.event_history = EventHistory()
        self.model_to_history = dict()

    # This method will be called to initialize the manager
    def start(self):
        print 'EVENT MANAGER - STARTING'

        print 'Event types registered: ', len(self.event_types)

        print 'EVENT MANAGER - STARTED'

    # This method will be called to shutdown the manager
    def stop(self):
        print 'EVENT MANAGER - STOPPING'

        print 'EVENT MANAGER - STOPPED'

    def add_event_class(self, event_class):
        '''
        Registers the given event class so that it can be used when converting raw log entries.

        Args:
           event_class (class): Event class definition.

        Returns:
            None
        '''

        assert event_class and event_class.TYPE and event_class.CALLBACK, (
                'Invalid event class: %s' % event_class)

        # Make sure the event constants are valid
        event_type = event_class.TYPE
        event_callback = event_class.CALLBACK
        assert len(event_type) == 2, 'Invalid event TYPE: %s' % event_type
        assert len(event_callback) > 0, 'Invalid event CALLBACK: %s' % event_callback

        # Make sure the type is not already registered
        assert not event_type in self.event_types, 'Duplicate event TYPE: %s' % event_type
        self.event_types[event_type] = event_class

    def create_event(self, line):
        '''
        Takes in a log line and converts it into a type-safe event model more convenient to use.

        Args:
            line (string): Raw log line from Battlefield 2 mod.

        Returns:
            event (BaseEvent): Returns an event data structure dependent on the log entry type.
        '''

        if not line: return

        # Break the line into individual elements
        elements = line.split(';')
        assert len(elements) > 1, 'Invalid log line %s' % line

        # Extract the log time and type
        time = int(elements[0])
        event_type = str(elements[1])
        values = elements[2:]

        # Check whether a log error was detected
        if event_type == 'ER':
            print 'ERROR - Invalid log entry detected: ', values
            return

        # Decode special case values
        values = [self._decode(value) for value in values]
 
        try:

            # Attempt to convert the values into a type-safe event model
            event_class = self.event_types[event_type]
            event = event_class(time, values)

            # Reset the event history when a new game starts
            if isinstance(event, GameStatusEvent) and event.game.starting:
                self.reset_history()

            # Register the event with the global history system
            self.event_history.add_event(event)
            return event
        except KeyError:
            print 'Unknown event type: ', event_type

    def get_history(self, model=None):
        '''
        Gets the event history for the given model or gets the global event history if no model is
        provided.

        Args:
            model (object): Model for various Battlefield entities such as players, vehicles,
                    weapons, etc. None is equivalent to the global event history.

        Returns:
            history (EventHistory): The event history for the given model.
        '''

        # Use the global history if no model is given
        if not model: return self.event_history

        # Get the history for the given model
        if not model in self.model_to_history:
            self.model_to_history[model] = EventHistory()
        return self.model_to_history[model]

    def get_last_kit(self, player):
        '''
        Gets the last known kit model for the given player based on the tracked
        event history system. This convenience function is useful because kits
        are dropped as soon as a player gets killed, which means the kit
        information is not always readily available in certain cases such as
        when final death actually occurs.

        Args:
            player (Player): The player model for which to get a kit.

        Returns:
            kit (Kit): The last known kit for the player determined by looking
            up the most recent KitPickupEvent from the history system.
        '''

        if not player: return models.kits.EMPTY

        # Get the event history for the given player
        player_history = self.get_history(player)

        # Get the event that defines the last known kit for the player
        kit_event = player_history.get_new_event(KitPickupEvent.TYPE)
        return kit_event.kit if kit_event else models.kits.EMPTY

    def get_last_vehicle(self, player):
        '''
        Gets the last known vehicle model for the given player based on the
        tracked event history system. This convenience function is useful
        because vehicles are exited as soon as a player gets killed, which means
        the vehicle information is not always readily available in certain cases
        such as when final death actually occurs.

        Args:
            player (Player): The player model for which to get a vehicle.

        Returns:
            vehicle (Vehicle): The last known vehicle for the player determined
            by looking up the most recent VehicleEnterEvent from the history
            system.
        '''

        if not player: return models.vehicles.EMPTY

        # Get the event history for the given player
        player_history = self.get_history(player)

        # Get the event that defines the last known vehicle for the player
        vehicle_event = player_history.get_new_event(VehicleEnterEvent.TYPE)
        return vehicle_event.vehicle if vehicle_event else models.vehicles.EMPTY

    def reset_history(self):
        '''
        Resets all the event history. This is typically only called when a new game starts.

        Args:
           None

        Returns:
            None
        '''

        self.event_history = EventHistory()
        self.model_to_history.clear()

    def parse_pos(self, position):
        '''
        Takes a string of position values and converts it into an array of type-safe floating point
        coordinate values.

        Args:
           position (string): Position values to parse.

        Returns:
            coordinates (array): Returns an array of parsed floating point coordinates.
        '''

        if not position: return [0, 0, 0, 0]

        values = position.split(',')
        assert len(values) == 4, 'Invalid position array size: %i' % len(values)

        return [float(value) for value in values]

    def _decode(self, value):
        if value == 'None':
            return None
        elif value == 'True':
            return True
        elif value == 'False':
            return False
        return value

# Create a shared singleton instance of the event manager
event_mgr = EventManager()

class BaseEvent(object):

    TYPE = None
    CALLBACK = None

    counter = 0

    def __init__(self, tick, values, arg_count):

        assert len(values) == arg_count, '%s - Wrong number of values (expected %i, got %i)' % (
                self.__class__.__name__, arg_count, len(values))

        self.id = BaseEvent.counter
        self.timestamp = int(round(time.time() * 1000))
        self.tick = tick

        BaseEvent.counter += 1

    def after(self, event):
        '''
        Checks whether this event occurs after the given event, based on game tick time.

        Args:
           event (BaseEvent): The event to compare.

        Returns:
            result (boolean): Returns True if this event is after the given event, False otherwise.
        '''

        if event and event.tick:
            return self.tick > event.tick
        return False

    def before(self, event):
        '''
        Checks whether this event occurs before the given event, based on game tick time.

        Args:
           event (BaseEvent): The event to compare.

        Returns:
            result (boolean): Returns True if this event is before the given event, False otherwise.
        '''

        if event and event.tick:
            return self.tick < event.tick
        return False

    def consec(self, event):
        '''
        Checks whether this event is consecutive relative to the given event, based on game tick
        time. The actual test used looks for events that have a time difference of exactly 1.

        Args:
           event (BaseEvent): The event to compare.

        Returns:
            result (boolean): Returns True if this event occurs within 1 game tick of the given
                    event, False otherwise.
        '''

        return self.elapsed(event) == 1

    def elapsed(self, event):
        '''
        Calculates the time elapsed between this event and the given event, based on game tick time.

        Args:
           event (BaseEvent): The event to compare.

        Returns:
            ticks (int): Returns the amount of elapsed time between the events.
        '''

        if event and event.tick:
            return abs(self.tick - event.tick)
        return 0

    def synched(self, event):
        '''
        Checks whether this event occurs simultaneously relative to the given event, based on game
        tick time.

        Args:
           event (BaseEvent): The event to compare.

        Returns:
            result (boolean): Returns True if this event is at the same time as the given event,
                    False otherwise.
        '''

        if event and event.tick:
            return self.tick == event.tick
        return False

class AccuracyEvent(BaseEvent):

    TYPE =  'AC'
    CALLBACK = 'on_accuracy'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.player = model_mgr.get_player_by_name(values[0])
        self.weapon = model_mgr.get_weapon(values[1])

        self.bullets_hit = int(values[2])
        self.bullets_fired = int(values[3])

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.weapon).add_event(self)
event_mgr.add_event_class(AccuracyEvent)

class AmmoEvent(BaseEvent):

    TYPE =  'AM'
    CALLBACK = 'on_ammo'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.receiver = model_mgr.get_player_by_name(values[0])
        self.receiver_pos = event_mgr.parse_pos(values[1])

        self.giver = model_mgr.get_player_by_name(values[2])
        self.giver_pos = event_mgr.parse_pos(values[3])

        event_mgr.get_history(self.receiver).add_event(self)
        event_mgr.get_history(self.giver).add_event(self)
event_mgr.add_event_class(AmmoEvent)

class AssistEvent(BaseEvent):

    TYPE =  'AS'
    CALLBACK = 'on_assist'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.assist_type = values[2]

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(AssistEvent)

class BanEvent(BaseEvent):

    TYPE =  'BN'
    CALLBACK = 'on_ban'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.player = model_mgr.get_player_by_name(values[0])
        self.duration = values[1]
        self.ban_type = values[2]

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(BanEvent)

class ChatEvent(BaseEvent):

    TYPE =  'CH'
    CALLBACK = 'on_chat'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.channel = values[0]
        self.player = model_mgr.get_player_by_name(values[1])
        self.text = values[2]

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(ChatEvent)

class ClockLimitEvent(BaseEvent):

    TYPE =  'CL'
    CALLBACK = 'on_clock_limit'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 1)

        self.value = values[0]
event_mgr.add_event_class(ClockLimitEvent)

class CommanderEvent(BaseEvent):

    TYPE =  'CM'
    CALLBACK = 'on_commander'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.team = model_mgr.get_team(values[0])
        self.player = model_mgr.get_player_by_name(values[1])
        self.old_player = model_mgr.get_player(self.team.commander_id)

        event_mgr.get_history(self.team).add_event(self)
        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(CommanderEvent)

class ConnectEvent(BaseEvent):

    TYPE =  'CN'
    CALLBACK = 'on_connect'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        # Pre-process - Make sure the player model exists in the manager
        self.player = model_mgr.add_player(values[0], values[1])

        event_mgr.get_history(self.player).add_event(self)

event_mgr.add_event_class(ConnectEvent)

class ControlPointEvent(BaseEvent):

    TYPE =  'CP'
    CALLBACK = 'on_control_point'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        # Pre-process - Make sure the control point model exists in the manager
        self.control_point = model_mgr.add_control_point(
                model_mgr.get_game().map_id + values[1],
                event_mgr.parse_pos(values[1]))
        self.trigger_id = values[0]
        self.status = values[2]
        self.team = model_mgr.get_team(values[3])

        event_mgr.get_history(self.control_point).add_event(self)
        event_mgr.get_history(self.team).add_event(self)
event_mgr.add_event_class(ControlPointEvent)

class DeathEvent(BaseEvent):

    TYPE =  'DT'
    CALLBACK = 'on_death'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(DeathEvent)

class DisconnectEvent(BaseEvent):

    TYPE =  'DC'
    CALLBACK = 'on_disconnect'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        # Pre-process - Make sure the player model exists in the manager
        self.player = model_mgr.remove_player(values[0], values[1])

        event_mgr.get_history(self.player).add_event(self)

event_mgr.add_event_class(DisconnectEvent)

class FlagActionEvent(BaseEvent):

    TYPE =  'FA'
    CALLBACK = 'on_flag_action'

    CAPTURE = 'capture'
    CAPTURE_ASSIST = 'capture_assist'
    NEUTRALIZE = 'neutralize'
    NEUTRALIZE_ASSIST = 'neutralize_assist'
    DEFEND = 'defend'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.player = model_mgr.get_player_by_name(values[0])
        self.action_type = values[1]

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(FlagActionEvent)

class GameStatusEvent(BaseEvent):

    TYPE =  'GS'
    CALLBACK = 'on_game_status'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        # Pre-process - Make sure the game model exists in the manager
        self.game = model_mgr.set_game_status(values[0], values[1], int(values[2]), int(values[3]))

        event_mgr.get_history(self.game).add_event(self)

event_mgr.add_event_class(GameStatusEvent)

class HealEvent(BaseEvent):

    TYPE =  'HL'
    CALLBACK = 'on_heal'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.receiver = model_mgr.get_player_by_name(values[0])
        self.receiver_pos = event_mgr.parse_pos(values[1])
        self.giver = model_mgr.get_player_by_name(values[2])
        self.giver_pos = event_mgr.parse_pos(values[3])

        event_mgr.get_history(self.receiver).add_event(self)
        event_mgr.get_history(self.giver).add_event(self)
event_mgr.add_event_class(HealEvent)

class KickEvent(BaseEvent):

    TYPE =  'KC'
    CALLBACK = 'on_kick'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 1)

        self.player = model_mgr.get_player_by_name(values[0])

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(KickEvent)

class KillEvent(BaseEvent):

    TYPE =  'KL'
    CALLBACK = 'on_kill'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 6)

        self.victim = model_mgr.get_player_by_name(values[0])
        self.victim_pos = event_mgr.parse_pos(values[1])
        self.attacker = model_mgr.get_player_by_name(values[2])
        self.attacker_pos = event_mgr.parse_pos(values[3])
        self.weapon = model_mgr.get_weapon(values[4])
        self.vehicle = model_mgr.get_vehicle(values[5])

        self.suicide = (self.victim == self.attacker)
        self.team_kill = ((self.suicide == False)
                and (self.victim.team_id == self.attacker.team_id))
        self.valid_kill = (self.suicide == False and self.team_kill == False)

        event_mgr.get_history(self.victim).add_event(self)
        event_mgr.get_history(self.attacker).add_event(self)
        event_mgr.get_history(self.weapon).add_event(self)
event_mgr.add_event_class(KillEvent)

class KitDropEvent(BaseEvent):

    TYPE =  'KD'
    CALLBACK = 'on_kit_drop'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.kit = model_mgr.get_kit(values[2])

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.kit).add_event(self)
event_mgr.add_event_class(KitDropEvent)

class KitPickupEvent(BaseEvent):

    TYPE =  'KP'
    CALLBACK = 'on_kit_pickup'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.kit = model_mgr.get_kit(values[2])

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.kit).add_event(self)
event_mgr.add_event_class(KitPickupEvent)

class LossEvent(BaseEvent):

    TYPE =  'LS'
    CALLBACK = 'on_loss'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.team = model_mgr.get_team(values[0])
        self.condition_id = values[1]

        event_mgr.get_history(self.team).add_event(self)
event_mgr.add_event_class(LossEvent)

class RepairEvent(BaseEvent):

    TYPE =  'RP'
    CALLBACK = 'on_repair'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.vehicle = model_mgr.get_vehicle(values[0])
        self.vehicle_pos = event_mgr.parse_pos(values[1])
        self.giver = model_mgr.get_player_by_name(values[2])
        self.giver_pos = event_mgr.parse_pos(values[3])

        event_mgr.get_history(self.vehicle).add_event(self)
        event_mgr.get_history(self.giver).add_event(self)
event_mgr.add_event_class(RepairEvent)

class ResetEvent(BaseEvent):

    TYPE =  'RS'
    CALLBACK = 'on_reset'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 1)

        self.data = values[0]
event_mgr.add_event_class(ResetEvent)

class ReviveEvent(BaseEvent):

    TYPE =  'RV'
    CALLBACK = 'on_revive'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.receiver = model_mgr.get_player_by_name(values[0])
        self.receiver_pos = event_mgr.parse_pos(values[1])
        self.giver = model_mgr.get_player_by_name(values[2])
        self.giver_pos = event_mgr.parse_pos(values[3])

        event_mgr.get_history(self.receiver).add_event(self)
        event_mgr.get_history(self.giver).add_event(self)
event_mgr.add_event_class(ReviveEvent)

class ScoreEvent(BaseEvent):

    TYPE =  'SC'
    CALLBACK = 'on_score'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.player = model_mgr.get_player_by_name(values[0])
        self.value = int(values[1])

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(ScoreEvent)

class ServerStatusEvent(BaseEvent):

    TYPE =  'SS'
    CALLBACK = 'on_server_status'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.status = values[0]
        self.status_time = values[1]

        model_mgr.set_server_status(values[0], values[1])

event_mgr.add_event_class(ServerStatusEvent)

class SpawnEvent(BaseEvent):

    TYPE =  'SP'
    CALLBACK = 'on_spawn'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.team = model_mgr.get_team(values[2])

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.team).add_event(self)
event_mgr.add_event_class(SpawnEvent)

class SquadEvent(BaseEvent):

    TYPE =  'SQ'
    CALLBACK = 'on_squad'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.player = model_mgr.get_player_by_name(values[0])

        # Pre-process - Make sure the squad model exists in the manager
        self.squad = model_mgr.add_squad(values[1])

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(SquadEvent)

class SquadLeaderEvent(BaseEvent):

    TYPE =  'SL'
    CALLBACK = 'on_squad_leader'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        # Pre-process - Make sure the squad model exists in the manager
        self.squad = model_mgr.add_squad(values[0])
        self.player = model_mgr.get_player_by_name(values[1])
        self.old_player = model_mgr.get_player(self.squad.leader_id)

        event_mgr.get_history(self.player).add_event(self)
event_mgr.add_event_class(SquadLeaderEvent)

class TeamDamageEvent(BaseEvent):

    TYPE =  'TD'
    CALLBACK = 'on_team_damage'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.victim = model_mgr.get_player_by_name(values[0])
        self.victim_pos = event_mgr.parse_pos(values[1])
        self.attacker = model_mgr.get_player_by_name(values[2])
        self.attacker_pos = event_mgr.parse_pos(values[3])

        event_mgr.get_history(self.victim).add_event(self)
        event_mgr.get_history(self.attacker).add_event(self)
event_mgr.add_event_class(TeamDamageEvent)

class TeamEvent(BaseEvent):

    TYPE =  'TM'
    CALLBACK = 'on_team'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.player = model_mgr.get_player_by_name(values[0])
        self.team = model_mgr.get_team(values[1])

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.team).add_event(self)
event_mgr.add_event_class(TeamEvent)

class TicketLimitEvent(BaseEvent):

    TYPE =  'TL'
    CALLBACK = 'on_ticket_limit'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.team = model_mgr.get_team(values[0])
        self.value = int(values[1])

        event_mgr.get_history(self.team).add_event(self)
event_mgr.add_event_class(TicketLimitEvent)

class VehicleDestroyEvent(BaseEvent):

    TYPE =  'VD'
    CALLBACK = 'on_vehicle_destroy'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 5)

        self.vehicle = model_mgr.get_vehicle(values[0])
        self.vehicle_pos = event_mgr.parse_pos(values[1])
        self.attacker = model_mgr.get_player_by_name(values[2])
        self.attacker_pos = event_mgr.parse_pos(values[3])
        self.driver = model_mgr.get_player_by_name(values[4])

        event_mgr.get_history(self.vehicle).add_event(self)
        event_mgr.get_history(self.attacker).add_event(self)
        event_mgr.get_history(self.driver).add_event(self)
event_mgr.add_event_class(VehicleDestroyEvent)

class VehicleEnterEvent(BaseEvent):

    TYPE =  'VE'
    CALLBACK = 'on_vehicle_enter'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 5)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.vehicle = model_mgr.get_vehicle(values[2])
        self.vehicle_slot_id = values[3]
        self.free_soldier = values[4]

        if self.vehicle_slot_id and not self.vehicle_slot_id in self.vehicle.slot_ids:
            print ('ERROR - Missing vehicle slot reference: %s -> %s'
                    % (self.vehicle.id, self.vehicle_slot_id))

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.vehicle).add_event(self)
event_mgr.add_event_class(VehicleEnterEvent)

class VehicleExitEvent(BaseEvent):

    TYPE =  'VX'
    CALLBACK = 'on_vehicle_exit'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 4)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.vehicle = model_mgr.get_vehicle(values[2])
        self.vehicle_slot_id = values[3]

        if self.vehicle_slot_id and not self.vehicle_slot_id in self.vehicle.slot_ids:
            print ('ERROR - Missing vehicle slot reference: %s -> %s'
                    % (self.vehicle.id, self.vehicle_slot_id))

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.vehicle).add_event(self)
event_mgr.add_event_class(VehicleExitEvent)

class WeaponEvent(BaseEvent):

    TYPE =  'WP'
    CALLBACK = 'on_weapon'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 3)

        self.player = model_mgr.get_player_by_name(values[0])
        self.player_pos = event_mgr.parse_pos(values[1])
        self.weapon = model_mgr.get_weapon(values[2])

        event_mgr.get_history(self.player).add_event(self)
        event_mgr.get_history(self.weapon).add_event(self)
event_mgr.add_event_class(WeaponEvent)

class WinEvent(BaseEvent):

    TYPE =  'WN'
    CALLBACK = 'on_win'

    def __init__(self, tick, values):
        BaseEvent.__init__(self, tick, values, 2)

        self.team = model_mgr.get_team(values[0])
        self.condition_id = values[1]

        event_mgr.get_history(self.team).add_event(self)
event_mgr.add_event_class(WinEvent)
