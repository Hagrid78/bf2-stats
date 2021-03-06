﻿// Handles all the controller logic for the live front page
$(function() {

// Load the custom jQuery user interface components
$('.common-logger').logger();
var tickerElm = $('.ticker-widget').ticker();
var meterElm = $('.meter-widget').meter();
var mapElm = $('.olmap-widget');
var messageElm = $('.message-widget').message();

// Register the page manager as a jQuery extension
$.extend({ mgr: {

   controlPoints: {},
   mapMarkers: {},

   // Callback from the server when the game changes
   onGame: function(e, packet) {

      // Reset the meter
      meterElm.meter({ max: packet.game.clock_limit, value: 0});
      meterElm.meter('clearMarkers');

      // Reset the messages
      messageElm.message('clearMessages');

      // Clear previous map markers
      $.mgr.controlPoints = {};
      $.mgr.mapMarkers = {};
      mapElm.olmap('clearMarkers');

      // Set the new map tiles
      mapElm.olmap({ mapName: packet.game.map_id });
   },

   // Callback from the server when a player changes
   onPlayer: function(e, packet) {
      tickerElm.ticker('update', packet.player);
   },

   // Callback from the server when a control point is captured
   onControlPoint: function(e, packet) {

      // Remove the old control point state
      old = $.mgr.controlPoints[packet.control_point.id]
      mapElm.olmap('removePackets', old);

      // Add the new control point state to the map
      $.mgr.controlPoints[packet.control_point.id] = packet
      mapElm.olmap('addPackets', packet);
   },

   onFlagAction: function(e, packet) {

      // Add a meter marker when the control point changes state
      meterElm.meter('addPackets', packet);
   },

   // Callback from the server when a player is killed
   onKill: function(e, packet) {

      // Add a message describing the kill
      messageElm.message('addPackets', packet);

      // Add a map marker to represent the kill
      if (!$.mgr.mapMarkers[packet.tick]) {
         $.mgr.mapMarkers[packet.tick] = [];
      }
      $.mgr.mapMarkers[packet.tick].push(packet);
      mapElm.olmap('addPackets', packet);
   },

   // Callback from the server when game time elapses
   onTime: function(e, packet) {

      // Remove old map markers
      packets = []
      for (tick in $.mgr.mapMarkers) {
         if (packet.tick - tick >= 10) {
            packets = packets.concat($.mgr.mapMarkers[tick]);
            delete $.mgr.mapMarkers[tick];
         }
      }
      mapElm.olmap('removePackets', packets);

      // Move the meter to the current game time
      meterElm.meter({ value: packet.time });
   },

   // Callback from the server when a vehicle is destroyed
   onVehicleDestroy: function(e, packet) {

      // Add a message describing the destroy
      messageElm.message('addPackets', packet);

      // Add a map marker to represent the vehicle
      if (!$.mgr.mapMarkers[packet.tick]) {
         $.mgr.mapMarkers[packet.tick] = [];
      }
      $.mgr.mapMarkers[packet.tick].push(packet);
      mapElm.olmap('addPackets', packet);
   }

}});

// Configure the network callbacks
$($.service).on('GS', $.mgr.onGame);
$($.service).on('CP', $.mgr.onControlPoint);
$($.service).on('FA', $.mgr.onFlagAction);
$($.service).on('KL', $.mgr.onKill);
$($.service).on('PL', $.mgr.onPlayer);
$($.service).on('TT', $.mgr.onTime);
$($.service).on('VD', $.mgr.onVehicleDestroy);

// Start fetching data from the server
setTimeout(function() { $.service.refresh(); }, 2000);

});
