"""Support for Dawon Switch."""
import logging
import requests
import json
import urllib
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import callback
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.const import (CONF_NAME)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.util.json import load_json, save_json

_LOGGER = logging.getLogger(__name__)

CONF_USER_ID ='user_id'
CONF_ACCOUNT='user_account'
CONF_DEVICE_LIST = 'device_list'

ATTR_CURRENT_CONSUMPTION = 'current_consumption'
ATTR_CURRENT_CONSUMPTION_UNIT = 'current_consumption_unit'
ATTR_CURRENT_CONSUMPTION_UNIT_VALUE = 'w'
ATTR_TODAY_CONSUMPTION = 'monthly_consumption'
ATTR_TODAY_CONSUMPTION_UNIT = 'monthly_consumption_unit'
ATTR_TODAY_CONSUMPTION_UNIT_VALUE = 'kWh'

ATTR_SSO_TOKEN='hi9oIIvbTdhlu69mMVXeI'
ATTR_FCM_TOKEN='AAAAOuAULGYR+pepTchrN'
ATTR_TERMINAL_ID='1234567890'
TIMEOUT=5

DAWON_API_URL='https://dwapi.dawonai.com:18443'
DAWON_CONFIG_FILE = 'dawon.conf'
DAWON_EMAIL='none'
DAWON_NAME='none'

DEFAULT_NAME = 'Dawon'
DEFAULT_ACCOUNT = 'google'
DEFALUT_ICON = 'mdi:power-socket-eu'

DEPENDENCIES = ['http']

_MON_COND = {
    'value_watt': ['Watt', 'Usage', 'w', 'mdi:pulse', 'watt'],
    'value_watth': ['WattMonth', 'Usage', 'kWh', 'mdi:pulse', 'watt_month'],
    'conn_status': ['Connection', 'State', '', 'mdi:power-socket-eu', 'connection']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USER_ID): cv.string,
    vol.Required(CONF_ACCOUNT): cv.string,
    vol.Required(CONF_DEVICE_LIST):
     vol.All(cv.ensure_list),
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a Dawon Switch."""

    client_id = config.get(CONF_USER_ID)
    client_account = config.get(CONF_ACCOUNT)
    device_list = config.get(CONF_DEVICE_LIST)

    client = DawonAPI(client_id, client_account, hass.config.path(DAWON_CONFIG_FILE))

    client.get_session()
    switch = []
    sensors = []

    for device in device_list:
        switch += [DawonSwitch(client, device)]
        _LOGGER.debug('DEVICE : %s', device)

    for device in device_list:
        for variable in _MON_COND:
            _LOGGER.debug('SENSOR : {} {}'.format(variable, device))
            sensors += [DawonCurrentSensor(device, variable, _MON_COND[variable], client)]

    add_entities(switch, True)
    add_entities(sensors, True)


class DawonAPI:
    """DawonAPI."""

    def __init__(self, client_id, client_account, config_path):
        """Initialize the Client."""
        self.client_id = client_id
        self.client_account = client_account
        self.config_path = config_path
        self.session = 'none'
        self._value = {}

    def request_api(self, url, header, payload):
        url = DAWON_API_URL + url
        if type(header) == str:
            header = {'X-Requested-With': 'XMLHttpRequest',\
                    'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                    'Cookie': 'SESSION=' + header}
            body = urllib.parse.urlencode(payload)
            response = requests.post(url, headers=header, data=body, timeout=TIMEOUT)
            return response

    def get_session(self):
        import os
        if not os.path.isfile(self.config_path):
            return self.login_session()
        else:
            self.session = load_json(self.config_path)['SESSION']
            return self.session

    def login_session(self):
        first_session = self.get_cookie()
        url = '/iot/member/loginAction.opi'
        header = str(first_session['SESSION'])
        payload = {'user_id': self.client_id + '/' + self.client_account,
                    'sso_token': ATTR_SSO_TOKEN,
                    'fcm_token': ATTR_FCM_TOKEN,
                    'terminal_id': ATTR_TERMINAL_ID,
                    'os_type': 'Android',
                    'email': DAWON_EMAIL,
                    'name': DAWON_NAME,
                    'register': self.client_account,
                    'terminal_name': 'HomeAssistant'}
        response = self.request_api(url, header, payload)
        if response.text == 'Y':
            _LOGGER.debug('SESSION: %s', str(first_session['SESSION']))
            save_json(self.config_path, first_session)
            return str(first_session['SESSION'])
        _LOGGER.debug('Login Failed')
        return False

    def check_session(self, response_data):
        if 'intro.opi' in response_data.text:
            _LOGGER.debug('Refresh Session')
            self.login_session()
            return False
        else:
            return True

    def get_cookie(self):
        url = DAWON_API_URL + '/iot/'
        header={'Upgrade-Insecure-Requests':'1'}
        session = requests.Session()
        response = session.get(url, headers=header, timeout=TIMEOUT)
        _LOGGER.debug('Get Cookie')
        return response.cookies.get_dict()

    def get_status(self, device_id):
        url = '/iot/product/device_profile_get.opi'
        header = self.get_session()
        payload={'devicesId': device_id}
        response = self.request_api(url, header, payload)
        state = 'off'

        # 세션이 정상일 경우
        if self.check_session(response):
            try:
                state = 'on' if response.json()['devices'][0]['device_profile']['power'] == 'true' else 'off'
            except:
                state = 'off'
                pass
        # 휴대폰 앱에 로그인이 되어있는 경우 or 세션이 만료된 경우
        if response.status_code == 500 or not self.check_session(response):
            header = self.login_session()
            response = self.request_api(url, header, payload)
            try:
                state = 'on' if response.json()['devices'][0]['device_profile']['power'] == 'true' else 'off'
            except:
                state = 'off'
                pass
        _LOGGER.debug('state : %s', state)
        return True if state == 'on' else False

    def turn_onff(self, device_id, command):
        url = '/iot/product/device_' + command + '.opi'
        header = self.get_session()
        payload={'devicesId': device_id}
        response = self.request_api(url, header, payload)
        
        # 휴대폰 앱에 로그인이 되어있는 경우 or 세션이 만료된 경우
        if response.status_code == 500 or not self.check_session(response):
            header = self.login_session()
            response = self.request_api(url, header, payload)
        
        # 제어결과
        if 'execute success' in response.text:
            _LOGGER.debug('command : %s', command)
            return True
        return False

    def get_realtime(self, device_id):
        from websocket import create_connection
        ws = create_connection("wss://dwws.dawonai.com:18444/mqreceiver/v1/devices/webSocket")
        ws.send("deviceInfo;productList;" + device_id)
        buf =[]
        for x in range(3):
            result =  ws.recv()
            buf.append(result)
            if len(buf) == 2:
                if 'value_watt' in buf[1]:
                    value0 = json.loads(buf[0])
                    value1 = json.loads(buf[1])
                    value_json = {
                        'value_power': value0['value_power'],
                        'value_watt': value1['value_watt'],
                        'value_watth': value1['value_watth'],
                        'device_id': value1['device_id'],
                        'conn_status': value1['conn_status']
                    }
                    self._value[device_id] = value_json
                    return value_json
                    #_LOGGER.debug('{} {} {} {} {}'.format(value0["value_power"],value1["value_watt"],value1["value_watth"],value1["device_id"],value1["conn_status"]))
                    # buf[1] {"value_watt":"0.00","value_watth":"0.00000","device_id":"DAWONDNS-B530_W-827d3a1feeb0","conn_status":"1"}
                    # buf[0] {"value_power":"false","device_id":"DAWONDNS-B530_W-827d3a1feeb0","conn_status":"1"}
                ws.close()
                break

    def get_value(self, device_id):
        return self._value[device_id]

class DawonSwitch(SwitchDevice):
    """Representation of a Dawon Switch."""

    def __init__(self, client, device):
        """Initialize the Dawon Switch."""
        self.client = client
        self.device = device
        self._is_on = True if client.get_status(device) else False
        self._current_watt = 0.00
        self._month_watt = 0.00
        self._connection = 0
        self._device_id = device.split('-')[2]
        self._device_model = device.split('-')[1]

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'switch.dawondns_{}_{}'.format(self._device_model.lower(), self._device_id)

    @property
    def name(self):
        """Name of the device."""
        return '{} {}'.format(self._device_model, self._device_id)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return DEFALUT_ICON

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._is_on = True if self.client.turn_onff(self.device, 'on') else False

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._is_on = False if self.client.turn_onff(self.device, 'off') else False

    @property
    def device_info(self):
        return {
            'identifiers': {
                # Serial numbers are unique identifiers within a specific domain
                ('DAWON', self.unique_id)
            },
            'name': self.device,
            'manufacturer': 'DAWONDNS',
            'model': 'DAWONDNS-B530',
            'sw_version': '0.0.1',
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {}
        if self.result:
            self._current_watt = float(self.result["value_watt"])
            self._month_watt = float(self.result["value_watth"])
            self._connection = self.result["conn_status"]

        attrs[ATTR_CURRENT_CONSUMPTION] = "{:,.2f}".format(self._current_watt)
        attrs[ATTR_CURRENT_CONSUMPTION_UNIT] = "{}".format(ATTR_CURRENT_CONSUMPTION_UNIT_VALUE)
        attrs[ATTR_TODAY_CONSUMPTION] = "{:,.2f}".format(float(self._month_watt))
        attrs[ATTR_TODAY_CONSUMPTION_UNIT] = "{}".format(ATTR_TODAY_CONSUMPTION_UNIT_VALUE)
        attrs['model'] = "{}".format(self._device_model)
        attrs['id'] = "{}".format(self._device_id)
        attrs['connection'] = 'connected' if self._connection == '1' else 'disconnected'
        return attrs

    def update(self):
        """Get the latest value"""
        if self.client.get_session():
            self.result = self.client.get_realtime(self.device)
            if self.result and self.result["value_power"]:
                self._is_on = True if self.result["value_power"] == 'true' else False

class DawonSensor(Entity):
    """Representation of a Dawon Sensor."""

    def __init__(self, device, variable, variable_info):
        """Initialize the Dawon sensor."""
        self._device = device
        self.var_id = variable
        self.var_entity = variable_info[4]
        self.var_period = variable_info[0]
        self.var_type = variable_info[1]
        self.var_units = variable_info[2]
        self.var_icon = variable_info[3]
        self._device_id = device.split('-')[2]
        self._device_model = device.split('-')[1]

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.dawondns_{}_{}_{}'.format(self._device_model.lower(), self._device_id, self.var_entity)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return '{} {}({})'.format(self._device_model, self.var_period, self._device_id)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self.var_icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self.var_units

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            'name': self._device,
            'manufacturer': 'DAWONDNS',
            'model': self._device_model,
            'sw_version': '0.0.2',
        }

class DawonCurrentSensor(DawonSensor):
    """Representation of a Dawon Current Sensor."""

    def __init__(self, device, variable, variable_info, client):
        """Initialize the Dawon Current Sensor."""
        super().__init__(device, variable, variable_info)
        self.client = client
        self.result = {}
        self._power = 'false'
        self._current_watt = 0.00
        self._month_watt = 0.00
        self._connection = 0

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.var_id == 'value_watt':
            value ="{:,.2f}".format(self._current_watt) if self._power == 'true' else "{:,.2f}".format(0.00)
            return value
        if self.var_id == 'value_watth':
            value = "{:,.2f}".format(self._month_watt)
            return value
        if self.var_id == 'conn_status':
            return 'on' if self._connection == '1' else 'off'
        return self.result[self.var_id]

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return {
            'model': self._device_model,
            'id': self._device_id
        }

    def update(self):
        """Update function for updating api information."""
        if self.result is not None:
            self.result = self.client.get_value(self._device)
            if "value_watt" in self.result:
                self._current_watt = float(self.result["value_watt"])
            if "value_watth" in self.result:
                self._month_watt = float(self.result["value_watth"])
            if "conn_status" in self.result:
                self._connection = self.result["conn_status"]
            if "value_power" in self.result:
                self._power = self.result["value_power"]
