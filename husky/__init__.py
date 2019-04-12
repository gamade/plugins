#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2019 Markus Garscha                               mg@gama.de 
#########################################################################
#  This file is part of SmartHomeNG.   
#
#  Sample plugin for new plugins to run with SmartHomeNG version 1.4 and
#  upwards.
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from lib.module import Modules
from lib.model.smartplugin import *

import json
import requests 

from datetime import datetime, timedelta
from dateutil.parser import parse
from http.server import BaseHTTPRequestHandler
from collections import deque

# If a needed package is imported, which might be not installed in the Python environment,
# add it to a requirements.txt file within the plugin's directory


class Husky(SmartPlugin):
    """
    Main class of the Plugin. Does all plugin specific stuff and provides
    the update functions for the items
    """

    PLUGIN_VERSION = '1.6.0'

    ITEM_INFO = "husky_info"
    ITEM_CONTROL = "husky_control"
    ITEM_STATE  = "husky_state"

    VALID_INFOS = ['name','id','model']
    VALID_COMMANDS = ['start','stop','park']
    VALID_STATES = ['color','activity','message','batterypercent']

    STATUS = {
        "PARKED_PARKED_SELECTED"       :   {'color' :  '1874CD', 'activity' : 'PARKED',   'msg' : 'GEPARKT - Bis auf Weiteres'},
        "PARKED_TIMER"                 :   {'color' :  '1874CD', 'activity' : 'PARKED',   'msg' : 'GEPARKT - Nächste Startzeit {starttime_HM}'},
        "PARKED_AUTOTIMER"             :   {'color' :  '1874CD', 'activity' : 'PARKED',   'msg' : 'GEPARKT - PARKED_AUTOTIMER'},
        "COMPLETED_CUTTING_TODAY_AUTO" :   {'color' :  '1874CD', 'activity' : 'PARKED',   'msg' : 'GEPARKT - Wettertimer'},
        "OK_CUTTING"                   :   {'color' :  '38761D', 'activity' : 'CUTTING',  'msg' : 'MÄHEN - Mäheinsatz endet HH:MM'},
        "OK_CUTTING_NOT_AUTO"          :   {'color' :  '38761D', 'activity' : 'CUTTING',  'msg' : 'MÄHEN - Timer aufheben'},
        "OK_SEARCHING"                 :   {'color' :  '38761D', 'activity' : 'MOVING',   'msg' : 'MÄHEN - Auf dem Weg zur Ladestation'},
        "OK_LEAVING"                   :   {'color' :  '38761D', 'activity' : 'MOVING',   'msg' : 'MÄHEN - Verlässt Ladestation'},
        "OK_CHARGING"                  :   {'color' :  '1874CD', 'activity' : 'CHARGING', 'msg' : 'LADEN - Nächste Startzeit {starttime_HM}'},
        "PAUSED"                       :   {'color' :  'FFA500', 'activity' : 'PAUSED',   'msg' : 'PAUSIERT'},
        "OFF_HATCH_OPEN"               :   {'color' :  'FF0000', 'activity' : 'DISABLED', 'msg' : 'OFF_HATCH_OPEN'},
        "OFF_HATCH_CLOSED"             :   {'color' :  'FF0000', 'activity' : 'DISABLED', 'msg' : 'OFF_HATCH_CLOSED'},
        "ERROR"                        :   {'color' :  'FF0000', 'activity' : 'ERROR',    'msg' : 'ERROR'},
        "UNKNOWN"                      :   {'color' :  'FF0000', 'activity' : 'UNKNOWN',  'msg' : 'n.a.' }
    }

    STARTSOURCE = {
        "NO_SOURCE"                    :   {'id' :  1, 'title' : ''},
        "WEEK_TIMER"                   :   {'id' :  2, 'title' : ''},
        "MOWER_CHARGING"               :   {'id' :  2, 'title' : ''},
        "UNKNOWN"                      :   {'id' :  0, 'title' : 'n.a.' }
    }

    OPERATINGMODE = {
        "HOME"                         :   {'id' :  1, 'title' : ''},
        "AUTO"                         :   {'id' :  2, 'title' : ''},
        "UNKNOWN"                      :   {'id' :  0, 'title' : 'n.a.' }
    }

    MOWERERROR = {
        0                              :   {'msg' : 'no error', 'color' : '00FF00'},
        1                              :   {'msg' : 'outside mowing area', 'color' : 'FFA500'},
        2                              :   {'msg' : 'no loop signal', 'color' : 'FF0000'},
        4                              :   {'msg' : 'Problem loop sensor front', 'color' : 'FF0000'},
        5                              :   {'msg' : 'Problem loop sensor rear', 'color' : 'FF0000'},
        6                              :   {'msg' : 'Problem loop sensor', 'color' : 'FF0000'},
        7                              :   {'msg' : 'Problem loop sensor', 'color' : 'FF0000'},
        8                              :   {'msg' : 'wrong PIN-code', 'color' : '9932CC'},
        9                              :   {'msg' : 'locked in', 'color' : '1874CD'},
       10                              :   {'msg' : 'upside down', 'color' : '1874CD'},
       11                              :   {'msg' : 'low battery', 'color' : '1874CD'},
       12                              :   {'msg' : 'battery empty', 'color' : 'FFA500'},
       13                              :   {'msg' : 'no drive', 'color' : '1874CD'},
       15                              :   {'msg' : 'Mower raised', 'color' : '1874CD'},
       16                              :   {'msg' : 'trapped in charging station', 'color' : 'FFA500'},
       17                              :   {'msg' : 'charging station blocked', 'color' : 'FFA500'},
       18                              :   {'msg' : 'Problem shock sensor rear', 'color' : 'FF0000'},
       19                              :   {'msg' : 'Problem shock sensor front', 'color' : 'FF0000'},
       20                              :   {'msg' : 'Wheel motor blocked on the right', 'color' : 'FF0000'},
       21                              :   {'msg' : 'Wheel motor blocked on the left', 'color' : 'FF0000'},
       22                              :   {'msg' : 'Drive problem left', 'color' : 'FF0000'},
       23                              :   {'msg' : 'Drive problem right', 'color' : 'FF0000'},
       24                              :   {'msg' : 'Problem mower engine', 'color' : 'FF0000'},
       25                              :   {'msg' : 'Cutting system blocked', 'color' : 'FFA500'},
       26                              :   {'msg' : 'Faulty component connection', 'color' : 'FF0000'},
       27                              :   {'msg' : 'default settings', 'color' : 'FF0000'},
       28                              :   {'msg' : 'Memory defective', 'color' : 'FF0000'},
       30                              :   {'msg' : 'battery problem', 'color' : 'FF0000'},
       31                              :   {'msg' : 'STOP-button problem', 'color' : 'FF0000'},
       32                              :   {'msg' : 'tilt sensor problem', 'color' : 'FF0000'},
       33                              :   {'msg' : 'Mower tilted', 'color' : '1874CD'},
       35                              :   {'msg' : 'Wheel motor overloaded right', 'color' : 'FF0000'},
       36                              :   {'msg' : 'Wheel motor overloaded left', 'color' : 'FF0000'},
       37                              :   {'msg' : 'Charging current too high', 'color' : 'FF0000'},
       38                              :   {'msg' : 'Temporary problem', 'color' : 'FF0000'},
       42                              :   {'msg' : 'limited cutting height range', 'color' : 'FF0000'},
       43                              :   {'msg' : 'unexpected cutting height adjustment', 'color' : 'FF0000'},
       44                              :   {'msg' : 'unexpected cutting height adjustment', 'color' : 'FF0000'},
       45                              :   {'msg' : 'Problem drive cutting height', 'color' : 'FF0000'},
       46                              :   {'msg' : 'limited cutting height range', 'color' : 'FF0000'},
       47                              :   {'msg' : 'Problem drive cutting height', 'color' : 'FF0000'}
    }

    # performance: flächenleistung in qm/h
    # chargetime: durchschnittliche Ladezeit in Minuten
    # mowtime: durchschnittliche Mähzeit in Minuten
    MOWERMODEL = {
        "TBD-1"    :   {'product' : 'AM105',     'name' : 'AUTOMOWER® 105',      'performance' : 43,  'chargetime' : 50, 'mowtime' : 70},
        "E"        :   {'product' : 'AM420',     'name' : 'AUTOMOWER® 420',      'performance' : 92,  'chargetime' : 55, 'mowtime' : 105},
        "TBD-3"    :   {'product' : 'AM440',     'name' : 'AUTOMOWER® 440',      'performance' : 167, 'chargetime' : 75, 'mowtime' : 240},
        "TBD-4"    :   {'product' : 'AM310',     'name' : 'AUTOMOWER® 310',      'performance' : 56,  'chargetime' : 50, 'mowtime' : 60},
        "TBD-5"    :   {'product' : 'AM315',     'name' : 'AUTOMOWER® 315',      'performance' : 68,  'chargetime' : 50, 'mowtime' : 60},
        "L"        :   {'product' : 'AM315X',    'name' : 'AUTOMOWER® 315X',     'performance' : 73,  'chargetime' : 50, 'mowtime' : 60},
        "G"        :   {'product' : 'AM430X',    'name' : 'AUTOMOWER® 430X',     'performance' : 133, 'chargetime' : 65, 'mowtime' : 135},
        "TBD-7"    :   {'product' : 'AM435XAWD', 'name' : 'AUTOMOWER® 435X AWD', 'performance' : 146, 'chargetime' : -1, 'mowtime' : -1},
        "TBD-8"    :   {'product' : 'AM450X',    'name' : 'AUTOMOWER® 450X',     'performance' : 208, 'chargetime' : 75, 'mowtime' : 260},
        "TBD-9"    :   {'product' : 'AM520',     'name' : 'AUTOMOWER® 520',      'performance' : 92,  'chargetime' : -1, 'mowtime' : -1},
        "TBD-A"    :   {'product' : 'AM535AWD',  'name' : 'AUTOMOWER® 535 AWD',  'performance' : 146, 'chargetime' : -1, 'mowtime' : -1},
        "TBD-B"    :   {'product' : 'AM550',     'name' : 'AUTOMOWER® 550',      'performance' : 208, 'chargetime' : -1, 'mowtime' : -1},
        "UNKNOWN"  :   {'product' : 'UKN',       'name' : 'no name yet',         'performance' : 0,   'chargetime' : -1, 'mowtime' : -1}
    }


    def __init__(self, sh, *args, **kwargs):
        """
        Initalizes the plugin. The parameters describe for this method are pulled from the entry in plugin.conf.

        :param sh:  **Deprecated**: The instance of the smarthome object. For SmartHomeNG versions 1.4 and up: **Don't use it**!
        :param *args: **Deprecated**: Old way of passing parameter values. For SmartHomeNG versions 1.4 and up: **Don't use it**!
        :param **kwargs:**Deprecated**: Old way of passing parameter values. For SmartHomeNG versions 1.4 and up: **Don't use it**!

        If you need the sh object at all, use the method self.get_sh() to get it. There should be almost no need for
        a reference to the sh object any more.

        The parameters *args and **kwargs are the old way of passing parameters. They are deprecated. They are imlemented
        to support oder plugins. Plugins for SmartHomeNG v1.4 and beyond should use the new way of getting parameter values:
        use the SmartPlugin method get_parameter_value(parameter_name) instead. Anywhere within the Plugin you can get
        the configured (and checked) value for a parameter by calling self.get_parameter_value(parameter_name). It
        returns the value in the datatype that is defined in the metadata.
        """
        from bin.smarthome import VERSION
        if '.'.join(VERSION.split('.', 2)[:2]) <= '1.5':
            self.logger = logging.getLogger(__name__)

        # If an package import with try/except is done, handle an import error like this:

        # Exit if the required package(s) could not be imported
        # if not REQUIRED_PACKAGE_IMPORTED:
        #     self.logger.error("Unable to import Python package '<exotic package>'")
        #     self._init_complete = False
        #     return

        # get the parameters for the plugin (as defined in metadata plugin.yaml):
        #   self.param1 = self.get_parameter_value('param1')

        self.userid = self.get_parameter_value('userid')
        self.password = self.get_parameter_value('password')
        self.device = self.get_parameter_value('device')

        self.use_token = True
        self.token = "" 
        self.provider = "" 
        self.expire_date = datetime(1900,1,1) 

        self.mower = None
        self.mower_status_que = deque(maxlen=10) 

        self._items_control = []
        self._items_state  = []

        # cycle time in seconds, only needed, if hardware/interface needs to be
        # polled for value changes by adding a scheduler entry in the run method of this plugin
        # (maybe you want to make it a plugin parameter?)
        self._cycle = 60

        # Initialization code goes here
        self.mowapi = API()

        if self.use_token and self.token and self.expire_date < datetime.now():
            # expired token found
            self.logger.warn("token expired. create new one")

        if self.use_token and self.expire_date > datetime.now():
            # valid token found
            self.logger.info("valid token found and used for authentification")
            self.mowapi.set_token(self.token, self.provider)
        else:
            # do (re-)login
            self.logger.info("login with userid: {0}".format(self.userid))
            lifetime = self.mowapi.login(self.userid, self.password)
            self.logger.info("login lifetime %d" % lifetime)
            if self.use_token:
                self.token = self.mowapi.token
                self.provider = self.mowapi.provider
                self.expire_date = datetime.now() + timedelta(0, lifetime)
                self.logger.info("token updated")

        self.mowers = self.mowapi.list_robots()

        if not len(self.mowers):
            self.logger.error("No mower found.")
            self._init_complete = False
            return
        else:
            # list and select mower
            for mower in self.mowers:
                if mower['name'] == self.device or mower['id'] == self.device:
                    self.mower = mower
                    self.logger.info("NAME: {0}, ID: {1}, MODEL: {2}".format(mower['name'], mower['id'], mower['model'])) 

            # select first, if no match
            if self.mower is None:
                self.mower = self.mowers[0]
		
            self.mowapi.select_robot(self.mower['id'])		
            self.logger.info("SELECTED MOWER: NAME: {0}, ID: {1}".format(self.mower['name'], self.mower['id'])) 
            # self.logger.debug(json.dumps(self.mower, indent=4, sort_keys=True))

        # On initialization error use:
        #   self._init_complete = False
        #   return

        # The following part of the __init__ method is only needed, if a webinterface is being implemented:

        # if plugin should start even without web interface
        # self.init_webinterface()

        # if plugin should not start without web interface
        if not self.init_webinterface():
            self._init_complete = False

        return

    def run(self):
        """
        Run method for the plugin
        """
        self.logger.debug("Run method called")
        # setup scheduler for device poll loop   (disable the following line, if you don't need to poll the device. Rember to comment the self_cycle statement in __init__ as well
        self.scheduler_add('poll_device', self.poll_device, cycle=self._cycle)



        self.alive = True
        # if you need to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        """
        Stop method for the plugin
        """
        self.logger.debug("Stop method called")
        self.alive = False

    def parse_item(self, item):
        """
        Default plugin parse_item method. Is called when the plugin is initialized.
        The plugin can, corresponding to its attribute keywords, decide what to do with
        the item in future, like adding it to an internal array for future reference
        :param item:    The item to process.
        :return:        If the plugin needs to be informed of an items change you should return a call back function
                        like the function update_item down below. An example when this is needed is the knx plugin
                        where parse_item returns the update_item function when the attribute knx_send is found.
                        This means that when the items value is about to be updated, the call back function is called
                        with the item, caller, source and dest as arguments and in case of the knx plugin the value
                        can be sent to the knx with a knx write function within the knx plugin.
        """
        if self.has_iattr(item.conf, self.ITEM_CONTROL):
            self.logger.debug("parse CONTROL item: {}".format(item))

            value = self.get_iattr_value(item.conf, self.ITEM_CONTROL).lower()
            if value in self.VALID_COMMANDS:
                self.logger.debug("adding valid command item {0} to wachlist {1}={2} ".format(item, self.ITEM_CONTROL, item.conf[self.ITEM_CONTROL]))
                self._items_control.append(item)
                return self.update_item
            else:
                self.logger.error("command '{0}' invalid, use one of {1}".format(value, self.VALID_COMMANDS))

        if self.has_iattr(item.conf, self.ITEM_STATE):
            self.logger.debug("parse STATE item: {}".format(item))

            value = self.get_iattr_value(item.conf, self.ITEM_STATE).lower()
            if value in self.VALID_STATES:
                self.logger.debug("adding valid state item {0} to wachlist {1}={2} ".format(item, self.ITEM_STATE, item.conf[self.ITEM_STATE]))
                self._items_state.append(item)
                return self.update_item
            else:
                self.logger.error("value '{0}' invalid, use one of {1}".format(value, self.VALID_STATES))


    def parse_logic(self, logic):
        """
        Default plugin parse_logic method
        """
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def update_item(self, item, caller=None, source=None, dest=None):
        """
        Item has been updated

        This method is called, if the value of an item has been updated by SmartHomeNG.
        It should write the changed value out to the device (hardware/interface) that
        is managed by this plugin.

        :param item: item to be updated towards the plugin
        :param caller: if given it represents the callers name
        :param source: if given it represents the source
        :param dest: if given it represents the dest
        """
        if caller != self.get_shortname():
            # code to execute, only if the item has not been changed by this this plugin:
            self.logger.info("Update item: {}, item has been changed outside this plugin".format(item.id()))

            if self.has_iattr(item.conf, self.ITEM_CONTROL):
                self.logger.debug("update_item was called with item '{}' from caller '{}', source '{}' and dest '{}'".format(item, caller, source, dest))
                cmd = self.get_iattr_value(item.conf, self.ITEM_CONTROL).lower()
                ret = {
                    'park'        : self._control_mower_park,
                    'stop'        : self._control_mower_stop,
                    'start'       : self._control_mower_start,
                    'default'     : self.logger.error("called undefined control function") 
		}.get(cmd)()
                

    def poll_device(self):
        """
        Polls for updates of the device

        This method is only needed, if the device (hardware/interface) does not propagate
        changes on it's own, but has to be polled to get the actual status.
        It is called by the scheduler.
        """

        self.cur_mower_status = self.mowapi.status()

        self.logger.info("---------------------------------------------")
        # self.logger.debug("-- RAW JSON DATA")
        # self.logger.debug(json.dumps(self.cur_mower_status, indent=4, sort_keys=True))
        self.logger.info("-- PARSED DATA")
        self.logger.info("batteryPercent .......: {0}".format(self.cur_mower_status['batteryPercent']))
        self.logger.info("cachedSettingsUUID ...: {0}".format(self.cur_mower_status['cachedSettingsUUID']))
        self.logger.info("connected ............: {0}".format(self.cur_mower_status['connected']))
        self.logger.info("lastErrorCode ........: {0}".format(self.cur_mower_status['lastErrorCode']))
        self.logger.info("lastErrorCodeTimestamp: {0} ({1})".format(self.cur_mower_status['lastErrorCodeTimestamp'], datetime.utcfromtimestamp(self.cur_mower_status['lastErrorCodeTimestamp']).strftime('%Y-%m-%d %H:%M:%S')))
        self.logger.info("lastLocations ........: {0}".format(len(self.cur_mower_status['lastLocations'])))
        self.logger.info("lastLocation lat......: {0}".format(self.cur_mower_status['lastLocations'][0]['latitude']))
        self.logger.info("lastLocation lon......: {0}".format(self.cur_mower_status['lastLocations'][0]['longitude']))
        self.logger.info("mowerStatus ..........: {0}".format(self.cur_mower_status['mowerStatus']))
        self.logger.info("nextStartSource ......: {0}".format(self.cur_mower_status['nextStartSource']))
        self.logger.info("nextStartTimestamp ...: {0} ({1})".format(self.cur_mower_status['nextStartTimestamp'],datetime.utcfromtimestamp(self.cur_mower_status['nextStartTimestamp']).strftime('%Y-%m-%d %H:%M:%S')))
        self.logger.info("operatingMode ........: {0}".format(self.cur_mower_status['operatingMode']))
        self.logger.info("showAsDisconnected ...: {0}".format(self.cur_mower_status['showAsDisconnected']))
        self.logger.info("storedTimestamp ......: {0} ({1})".format(self.cur_mower_status['storedTimestamp'], datetime.fromtimestamp(self.cur_mower_status['storedTimestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')))
        self.logger.info("valueFound ...........: {0}".format(self.cur_mower_status['valueFound']))


        if len(self.mower_status_que):
            last_mower_status = self.mower_status_que[-1]
            if last_mower_status['storedTimestamp'] < self.cur_mower_status['storedTimestamp']:
                self.logger.debug("updated status received: insert current status to que")
                self.mower_status_que.append(self.cur_mower_status)
            else:
                self.logger.debug("status exists already in status que: no update needed")
                # TODO: only if no enforced updates confugured 
                return
        else:
            self.logger.debug("mower status que is empty: insert current status to que")
            self.mower_status_que.append(self.cur_mower_status)

        # self.logger.debug("len(mower_status_que): {0}".format(len(self.mower_status_que)))

        #TODO: calc MOWING time, 
        # - e.g. estimate blade change
        # - approx. mowing area
        # - mowing cycles per day, month, ... 
       
        #TODO: calc MOVING time

        self.logger.debug("found {0} state items to update".format(len(self._items_state)))
        for item in self._items_state:
            key = item.conf[self.ITEM_STATE]
            self.logger.debug("update item {0} of type {1} and key {2}".format(item.id(), item.type(), key))
            value = {
                'activity'        : self._get_mower_status_activity,
                'color'           : self._get_mower_status_color,
                'message'         : self._get_mower_status_message,
                'batterypercent'  : self._get_mower_status_battery_percent,
                'default'         : None
            }.get(key)()

            self.logger.debug("update item: set {0} to {1}".format(key, value))

            # if the plugin is a gateway plugin which may receive updates from several external sources,
            # the source should be included when updating the the value:
            #     item(device_value, self.get_shortname(), source=device_source_id)
            item(value, self.get_shortname())


    def _get_api_connection(self):
        return self.mowapi.connection()

    def _get_api_token(self):
        return self.token

    def _get_api_token_expire_date(self):
        return self.expire_date

    def _get_mower_id(self):
        return self.mower['id']

    def _get_mower_model(self):
        return self.MOWERMODEL.get(self.mower['model'], self.MOWERMODEL['UNKNOWN']).get('product')

    def _get_mower_model_name(self):
        return self.MOWERMODEL.get(self.mower['model'], self.MOWERMODEL['UNKNOWN']).get('name')

    def _get_mower_name(self):
        return self.mower['name']

    def _get_mower_status_battery_percent(self):
        return self.cur_mower_status['batteryPercent']

    def _get_mower_last_latitude(self):
        return self.cur_mower_status['lastLocations'][0]['latitude']

    def _get_mower_last_longitude(self):
        return self.cur_mower_status['lastLocations'][0]['longitude']

    def _get_mower_last_coordinates(self):
        coordinates = [] 
        for location in self.cur_mower_status['lastLocations']:
            coordinates.append("[{0},{1}]".format(location['longitude'],location['latitude']))
        return "[" + ",".join(coordinates) + "]"

    def _get_mower_status_timestamp(self):
        return self.cur_mower_status['storedTimestamp']

    def _get_mower_status_time(self):
        return datetime.fromtimestamp(self.cur_mower_status['storedTimestamp']).strftime('%Y-%m-%d %H:%M:%S')

    def _get_mower_status_activity(self):
        return self.STATUS.get(self.cur_mower_status['mowerStatus'], self.STATUS['UNKNOWN']).get('activity')

    def _get_mower_status_message(self):
        message_template = self.STATUS.get(self.cur_mower_status['mowerStatus'], self.STATUS['UNKNOWN']).get('msg')
        starttime_YMDHMS = datetime.utcfromtimestamp(self.cur_mower_status['nextStartTimestamp']).strftime('%Y-%m-%d %H:%M:%S')
        starttime_HMS = datetime.utcfromtimestamp(self.cur_mower_status['nextStartTimestamp']).strftime('%H:%M:%S')
        starttime_HM = datetime.utcfromtimestamp(self.cur_mower_status['nextStartTimestamp']).strftime('%H:%M')
        return message_template.format(starttime_YMDHMS=starttime_YMDHMS, starttime_HMS=starttime_HMS, starttime_HM=starttime_HM)

    def _get_mower_status_color(self):
        return self.STATUS.get(self.cur_mower_status['mowerStatus'], self.STATUS['UNKNOWN']).get('color')

    def _get_mower_last_error_message(self):
        return self.MOWERERROR.get(self.cur_mower_status['lastErrorCode'], self.MOWERERROR[0]).get('msg')

    def _get_mower_last_error_timestamp(self):
        return self.cur_mower_status['lastErrorCodeTimestamp']

    def _get_mower_last_error_time(self):
        return datetime.fromtimestamp(self.cur_mower_status['lastErrorCodeTimestamp']).strftime('%Y-%m-%d %H:%M:%S')

    def _is_mower_connected(self):
        return bool(self.cur_mower_status['connected'])

    def _control_mower_park(self):
        self.logger.debug("_control_park() triggered")
        self.mowapi.control('PARK')
        return True

    def _control_mower_start(self):
        self.logger.debug("_control_start() triggered")
        self.mowapi.control('START')
        return True

    def _control_mower_stop(self):
        self.logger.debug("_control_stop() triggered")
        self.mowapi.control('STOP')
        return True

    def init_webinterface(self):
        """"
        Initialize the web interface for this plugin

        This method is only needed if the plugin is implementing a web interface
        """
        try:
            self.mod_http = Modules.get_instance().get_module(
                'http')  # try/except to handle running in a core version that does not support modules
        except:
            self.mod_http = None
        if self.mod_http == None:
            self.logger.error("Not initializing the web interface")
            return False

        import sys
        if not "SmartPluginWebIf" in list(sys.modules['lib.model.smartplugin'].__dict__):
            self.logger.warning("Web interface needs SmartHomeNG v1.5 and up. Not initializing the web interface")
            return False

        # set application configuration for cherrypy
        webif_dir = self.path_join(self.get_plugin_dir(), 'webif')
        config = {
            '/': {
                'tools.staticdir.root': webif_dir,
            },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': 'static'
            }
        }

        # Register the web interface as a cherrypy app
        self.mod_http.register_webif(WebInterface(webif_dir, self),
                                     self.get_shortname(),
                                     config,
                                     self.get_classname(), self.get_instance_name(),
                                     description='')

        return True


    def disp_age(self, age):
        days = 0
        hours = 0
        minutes = 0
        seconds = age
        if seconds >= 60:
            minutes = int(seconds / 60)
            seconds = seconds - 60 * minutes
            if minutes > 59:
                hours = int(minutes / 60)
                minutes = minutes - 60 * hours
                if hours > 23:
                    days = int(hours / 24)
                    hours = hours - 24 * days
        return self.age_to_string(days, hours, minutes, seconds)


    def age_to_string(self, days, hours, minutes, seconds):
        s = ''
        if days > 0:
            s += str(int(days)) + ' '
            if days == 1:
                s += translate('Tag')
            else:
                s += translate('Tage')
            s += ', '
        if (hours > 0) or (s != ''):
            s += str(int(hours)) + ' '
            if hours == 1:
                s += translate('Stunde')
            else:
                s += translate('Stunden')
            s += ', '
        if (minutes > 0) or (s != ''):
            s += str(int(minutes)) + ' '
            if minutes == 1:
                s += translate('Minute')
            else:
                s += translate('Minuten')
            s += ', '
        if days > 0:
            s += str(int(seconds))
        else:
            s += str("%.2f" % seconds)
        s += ' ' + translate('Sekunden')
        return s


# ------------------------------------------
#    Webinterface of the plugin
# ------------------------------------------

import cherrypy
from jinja2 import Environment, FileSystemLoader


class WebInterface(SmartPluginWebIf):

    def __init__(self, webif_dir, plugin):
        """
        Initialization of instance of class WebInterface

        :param webif_dir: directory where the webinterface of the plugin resides
        :param plugin: instance of the plugin
        :type webif_dir: str
        :type plugin: object
        """
        self.logger = logging.getLogger(__name__)
        self.webif_dir = webif_dir
        self.plugin = plugin
        self.tplenv = self.init_template_environment()

    @cherrypy.expose
    def index(self, reload=None):
        """
        Build index.html for cherrypy

        Render the template and return the html file to be delivered to the browser

        :return: contents of the template after beeing rendered 
        """
        tmpl = self.tplenv.get_template('index.html')
        # add values to be passed to the Jinja2 template eg: tmpl.render(p=self.plugin, interface=interface, ...)
        return tmpl.render(p=self.plugin, device_count=len(self.plugin.mowers))

    @cherrypy.expose
    def mower_park(self):
        self.plugin._control_mower_park()

    @cherrypy.expose
    def mower_start(self):
        self.plugin._control_mower_start()

    @cherrypy.expose
    def mower_stop(self):
        self.plugin._control_mower_stop()


# ------------------------------------------
#    Communication API of the plugin
# ------------------------------------------
# credits to pyhusmow

class API:
    _API_IM = 'https://iam-api.dss.husqvarnagroup.net/api/v3/'
    # original
    _API_TRACK = 'https://amc-api.dss.husqvarnagroup.net/v1/'
    # new url with 'app' to use with extended commands
    # _API_TRACK = 'https://amc-api.dss.husqvarnagroup.net/app/v1/'
    _HEADERS = {'Accept': 'application/json', 'Content-type': 'application/json'}

    def __init__(self):
        # self.logger = logging.getLogger("main.automower")
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.device_id = None
        self.token = None
        self.provider = None
        self.connection = None

    def login(self, login, password):
        response = self.session.post(self._API_IM + 'token',
                                     headers=self._HEADERS,
                                     json={
                                         "data": {
                                             "attributes": {
                                                 "password": password,
                                                 "username": login
                                             },
                                             "type": "token"
                                         }
                                     })

        try:
            response.raise_for_status()
            self.logger.info('Logged in successfully')
            self.connection="CONNECTED"
        except HTTPError as e:
            status_code = e.response.status_code
            self.logger.info("LOGIN FAILED: Status Code: {0}".format(status_code))
            self.connection="LOGIN FAILED"

        json = response.json()
        self.set_token(json["data"]["id"], json["data"]["attributes"]["provider"])
        return json["data"]["attributes"]["expires_in"]

    def logout(self):
        response = self.session.delete(self._API_IM + 'token/%s' % self.token)
        response.raise_for_status()
        self.device_id = None
        self.token = None
        del (self.session.headers['Authorization'])
        self.logger.info('Logged out successfully')
        self.connection="LOGGED OUT"

    def set_token(self, token, provider):
        self.token = token
        self.provider = provider
        self.session.headers.update({
            'Authorization': "Bearer " + self.token,
            'Authorization-Provider': provider
        })

    def list_robots(self):
        response = self.session.get(self._API_TRACK + 'mowers', headers=self._HEADERS)
        response.raise_for_status()

        return response.json()

    def select_robot(self, mower):
        result = self.list_robots()
        if not len(result):
            raise CommandException('No mower found')
        if mower:
            for item in result:
                if item['name'] == mower or item['id'] == mower:
                    self.device_id = item['id']
                    break
            if self.device_id is None:
                raise CommandException('Could not find a mower matching %s' % mower)
        else:
            self.device_id = result[0]['id']

    def status(self):
        response = self.session.get(self._API_TRACK + 'mowers/%s/status' % self.device_id, headers=self._HEADERS)
        response.raise_for_status()

        return response.json()

    def geo_status(self):
        response = self.session.get(self._API_TRACK + 'mowers/%s/geofence' % self.device_id, headers=self._HEADERS)
        response.raise_for_status()

        return response.json()

    def control(self, command):
        if command not in ['PARK', 'STOP', 'START']:
            raise CommandException("Unknown command")

        #TODO:
        # Park until further notice: 
        # /mower-id/control/park
        #
        # Park until next start
        # /mower-id/control/park/duration/timer
        #
        # Park with duration 
        # /mower-id/control/park/duration/period
        # 
        # Start main area
        # /mower-id/control/start
        # 
        # Start main area override timer
        # /mower-id/control/start/override/timer
        # json param: duration

        # PARK
        # mit nächstem Timer starten 
        # .../control/park/duration/timer
        # .../control/park/duration/period ("period" in Minuten im HEADER)

        # START 
        # .../control/start/override/period ("period" in Minuten im HEADER)

	# "period": 360
	# "period": 720

        # RESPONSE
        # "commandId": "...",
        # "errorCode": null,
        # "status": "OK"

        # TODO: new commands
        CMD = {
            'PARK'        : { 'url' : 'mowers/{device_id}/control',                  'json' : { 'action': 'PARK'} },
            'PARK_TIMER'  : { 'url' : 'mowers/{device_id}/control/park/duration/timer',   'json' : { 'action': 'PARK'} },
            'PARK_3H'     : { 'url' : 'mowers/{device_id}/control/park/duration/period',  'json' : { 'period': 180} },
            'PARK_6H'     : { 'url' : 'mowers/{device_id}/control/park/duration/period',  'json' : { 'period': 360} },
            'PARK_12H'    : { 'url' : 'mowers/{device_id}/control/park/duration/period',  'json' : { 'period': 720} },
            'START'       : { 'url' : 'mowers/{device_id}/control',                 'json' : { 'action': 'START'} },
            'START_3H'    : { 'url' : 'mowers/{device_id}/control/start/override/period', 'json' : { 'period': 180} },
            'START_6H'    : { 'url' : 'mowers/{device_id}/control/start/override/period', 'json' : { 'period': 360} },
            'START_12H'   : { 'url' : 'mowers/{device_id}/control/start/override/period', 'json' : { 'period': 720} },
            'STOP'        : { 'url' : 'mowers/{device_id}/control',                  'json' : { 'action': 'STOP'} }
        }

        #response = self.session.post(self._API_TRACK + 'mowers/%s/control' % self.device_id,
        #                            headers=self._HEADERS,
        #                            json={
        #                                "action": command
        #                            })
        response = self.session.post(self._API_TRACK + CMD[command]['url'].format(device_id=self.device_id),
                                     headers=self._HEADERS,
                                     json=CMD[command]['json'])
        response.raise_for_status()
        
        if (response.json()['status']=='OK'):
            return True
        else:
            self.logger.error("ERROR on posting action command '{0}': errorCode={1}".format(command, response.json()['errorCode']))
            # self.logger.debug(json.dumps(response.json(), indent=4, sort_keys=True))
            return False




