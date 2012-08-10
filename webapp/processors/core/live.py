﻿
import os

import models

from models import model_mgr
from processors import BaseProcessor
from stats import stat_mgr

class Processor(BaseProcessor):

    def __init__(self):
        BaseProcessor.__init__(self)

        self.priority = 30
        self.tick_to_packets = dict()
        self.start_tick = None
        self.last_tick = None

    def get_packets(self, packet_type, tick):

        # Check whether any packets have been received
        packets = list()
        if self.last_tick == None:
            return packets

        # Check whether the full game state is needed
        if not tick or tick > self.last_tick:

            # Generate a snapshot of the current game
            packets.extend(self._get_packet_list())
        elif tick != self.last_tick:
 
            # Add all the packets received since the given tick
            for i in range(tick + 1, self.last_tick + 1):
                if i in self.tick_to_packets:
                    packets.extend(self.tick_to_packets[i])

        # Filter the list of packets based on the given type
        if packet_type and len(packets) > 0:
            packets = filter(lambda p: p.type == packet_type, packets)

        # Add a packet to represent the next tick threshold
        if self.last_tick:
            packets.append(self._get_tick_packet())
        return packets

    def on_assist(self, e):

        # Create a packet to store the event info
        packet = self._get_stats_packet(e.player, ['teamwork'])
        self._add_packet(e.tick, packet)

    def on_connect(self, e):

        # Create a packet to store the event info
        packet = self._get_player_stats_packet(e.player)
        self._add_packet(e.tick, packet)

    def on_control_point(self, e):

        # Create a packet to store the event info
        packet = self._get_control_point_packet(e.control_point)
        self._add_packet(e.tick, packet)

    def on_death(self, e):

        # Create a packet to store the event info
        packet = self._get_stats_packet(e.player, ['deaths'])
        self._add_packet(e.tick, packet)

    def on_disconnect(self, e):

        # Create a packet to store the event info
        packet = self._get_player_packet(e.player, ['connected'])
        self._add_packet(e.tick, packet)

    def on_game_status(self, e):
        if e.game.starting:

            # Store the game start tick to calculate elapsed time
            self.start_tick = e.tick

            # Clear cached packets when the game resets
            self.tick_to_packets.clear()
            self.last_tick = None
        elif e.game.playing:

            # Create a packet to store the event info
            packet = self._get_game_packet(e.game)
            self._add_packet(e.tick, packet)

            # Add the player stats after the game reset
            for player in model_mgr.get_players(True):
                self._add_packet(e.tick, self._get_stats_packet(player))

    def on_heal(self, e):

        # Create a packet to store the event info
        packet = self._get_stats_packet(e.giver, ['teamwork'])
        self._add_packet(e.tick, packet)

    def on_kill(self, e):

        # Create a packet to store the event info
        kill_packet = {
            'tick': e.tick,
            'type': 'KL',
            'victim': self._get_kill_tuple(e.victim, e.victim_pos),
            'attacker': self._get_kill_tuple(e.attacker, e.attacker_pos,
                    e.weapon)
        }
        self._add_packet(e.tick, kill_packet)

        # Create a packet to store the attacker kills
        if e.attacker != models.players.EMPTY:
            attacker_packet = self._get_stats_packet(e.attacker, ['kills'])
            self._add_packet(e.tick, attacker_packet)

    def on_repair(self, e):

        # Create a packet to store the event info
        packet = self._get_stats_packet(e.giver, ['teamwork'])
        self._add_packet(e.tick, packet)

    def on_revive(self, e):

        # Create a packet to store the event info
        packet = self._get_stats_packet(e.giver, ['teamwork'])
        self._add_packet(e.tick, packet)

    def on_spawn(self, e):

        # Create a packet to store the event info
        packet = self._get_player_packet(e.player, ['team_id'])
        self._add_packet(e.tick, packet)

    def on_score(self, e):

        # Create a packet to store the event info
        packet = self._get_stats_packet(e.player,
                ['place', 'rank', 'score', 'trend'])
        self._add_packet(e.tick, packet)

    def on_vehicle_destroy(self, e):

        # Create a packet to store the event info
        packet = self._get_vehicle_packet(e.tick, e.vehicle, e.vehicle_pos)
        self._add_packet(e.tick, packet)

    def _add_packet(self, tick, packet):
        if tick not in self.tick_to_packets:
            self.tick_to_packets[tick] = list()
        self.tick_to_packets[tick].append(packet)
        self.last_tick = max(self.last_tick, tick)

    def _convert_x(self, x):
        return 8 * x + 8191

    def _convert_y(self, y):
        return 8 * y + 8191

    def _get_control_point_packet(self, control_point):
        control_point_tuple = {
            'id': control_point.id,
            'state': control_point.status,
            'team': control_point.team_id,
            'time': self._get_time(),
            'x': self._convert_x(control_point.pos[0]),
            'y': self._convert_y(control_point.pos[2])
        }

        return {
            'type': 'CP',
            'control_point': control_point_tuple
        }

    def _get_game_packet(self, game):
        game_tuple = {
            'id': game.id,
            'map_id': game.map_id,
            'clock_limit': game.clock_limit,
            'score_limit': game.score_limit
        }

        return {
            'type': 'GS',
            'game': game_tuple
        }

    def _get_kill_tuple(self, player, pos=None, weapon=None):
        if player == models.players.EMPTY:
            return None

        # Get the basic information for the player
        player_tuple = self._get_player_tuple(player)

        # Add position coordinates
        if pos:
            player_tuple['x'] = self._convert_x(pos[0])
            player_tuple['y'] = self._convert_y(pos[2])

        # Add weapon info
        if weapon:
            player_tuple['weapon'] = {
                'id': weapon.id,
                'name': weapon.name
            }
        return player_tuple

    def _get_packet_list(self):
        packets = list()

        # Add the current game info
        game = model_mgr.get_game()
        packets.append(self._get_game_packet(game))

        # Add the current player info
        for player in model_mgr.get_players(True):
            packets.append(self._get_player_stats_packet(player))

        # Add the current control point info
        for control_point in model_mgr.get_control_points(True):
            packets.append(self._get_control_point_packet(control_point))
        return packets

    def _get_player_packet(self, player, attributes=None):
        return {
            'type': 'PL',
            'player': self._get_player_tuple(player, attributes)
        }

    def _get_player_stats_packet(self, player):

        # Get the basic player info
        player_tuple = self._get_player_tuple(player)

        # Merge the stats in to the basic player info
        stats_tuple = self._get_stats_tuple(player)
        player_tuple.update(stats_tuple)

        return {
            'type': 'PL',
            'player': player_tuple
        }

    def _get_player_tuple(self, player, attributes=None):
        if attributes and len(attributes) > 0:
            player_tuple = {
                'id': player.id,
            }
            for attribute in attributes:
                player_tuple[attribute] = player.__dict__[attribute]
            return player_tuple

        return {
            'id': player.id,
            'name': player.name,
            'team_id': player.team_id,
            'photo_m': player.photo_m
        }

    def _get_stats_packet(self, player, attributes=None):
        return {
            'type': 'PL',
            'player': self._get_stats_tuple(player, attributes)
        }

    def _get_stats_tuple(self, player, attributes=None):
        player_stats = stat_mgr.get_player_stats(player)

        if attributes and len(attributes) > 0:
            stats_tuple = {
                'id': player.id
            }
            for attribute in attributes:
                stats_tuple[attribute] = player_stats.__dict__[attribute]
            return stats_tuple

        return {
            'id': player.id,
            'deaths': player_stats.deaths,
            'kills': player_stats.kills,
            'place': player_stats.place,
            'rank': player_stats.rank,
            'score': player_stats.score,
            'trend': player_stats.trend,
            'teamwork': player_stats.teamwork
        }

    def _get_tick_packet(self):
        return {
            'tick': self.last_tick,
            'type': 'TT',
            'time': self._get_time()
        }

    def _get_time(self):
        return self.last_tick - self.start_tick

    def _get_vehicle_packet(self, tick, vehicle, pos=None):
        vehicle_tuple = {
            'id': vehicle.id,
            'name': vehicle.name
        }

        if pos:
            vehicle_tuple['x'] = self._convert_x(pos[0])
            vehicle_tuple['y'] = self._convert_y(pos[2])

        return {
            'tick': tick,
            'type': 'VD',
            'vehicle': vehicle_tuple
        }
