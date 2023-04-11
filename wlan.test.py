from microtest import test, run, expect, mock_module, observe
from mocks import MockNetwork, MockWlan
import uasyncio
network = MockNetwork()
mock_module('network', network)
from wlan import Wlan, TimeoutException, InvalidPasswordException, AccessPointUnreachableException, ConnectionFailedException, STAT_NO_IP

@test
async def it_should_activate_the_wlan_interface_on_connect():
  (wlan, mock_wlan) = default_wlan_harness()
  mock_wlan.isconnected.returns(True)

  await wlan.connect()

  expect(mock_wlan.active).to_have_been_called_with(True)

@test
async def it_should_timeout_after_configured_period():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 1, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(network.STAT_CONNECTING)

  async def connect():
    await wlan.connect()

  await expect(connect).to_throw(TimeoutException)

@test
async def it_should_throw_an_invalid_password_error_immediately():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 5, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(network.STAT_WRONG_PASSWORD)

  async def connect():
    await wlan.connect()

  await expect(connect).to_throw(InvalidPasswordException)
  expect(mock_wlan.connect).to_have_been_called_times(1)

@test
async def it_should_throw_an_access_point_unreachable_error():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 1, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(network.STAT_NO_AP_FOUND)

  async def connect():
    await wlan.connect()

  await expect(connect).to_throw(AccessPointUnreachableException)

@test
async def it_should_throw_a_connection_failed_error():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 1, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(network.STAT_CONNECT_FAIL)

  async def connect():
    await wlan.connect()

  await expect(connect).to_throw(ConnectionFailedException)

@test
async def it_should_throw_an_os_error_when_an_unknown_status_is_received():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 1, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(38924)

  async def connect():
    await wlan.connect()

  await expect(connect).to_throw(OSError)

@test
async def it_should_retry_while_an_ip_address_is_being_assigned():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 5, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(STAT_NO_IP)
  mock_wlan.isconnected.define_returns(False, True)

  await wlan.connect()

  expect(mock_wlan.connect).to_have_been_called_times(2)

@test
async def it_should_retry_while_connecting_is_in_progress():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', retry_count = 5, timeout = 1, wlan = mock_wlan)
  mock_wlan.status.returns(network.STAT_CONNECTING)
  mock_wlan.isconnected.define_returns(False, True)

  await wlan.connect()

  expect(mock_wlan.connect).to_have_been_called_times(2)

@test
async def it_should_disable_power_saving_mode_on_connect():
  (wlan, mock_wlan) = default_wlan_harness()
  mock_wlan.isconnected.returns(True)

  await wlan.connect()

  expect(mock_wlan.config).to_have_been_called_with(pm = 0xA11140)

@test
async def it_should_trigger_the_on_connected_event_on_initial_connection():
  (wlan, mock_wlan) = default_wlan_harness()
  observer = observe(wlan.on_connected)
  mock_wlan.status.returns(network.STAT_CONNECTING)
  mock_wlan.isconnected.define_returns(False, True)

  await wlan.connect()
  await observer.wait()

  expect(observer).to_have_been_triggered()

@test
async def it_should_try_reconnecting_on_connection_loss():
  (wlan, mock_wlan) = default_wlan_harness()
  mock_wlan.status.returns(network.STAT_CONNECTING)
  mock_wlan.isconnected.define_returns(True, False)
  mock_wlan.isconnected.returns(True)

  await wlan.connect()
  await uasyncio.sleep(3)

  expect(mock_wlan.connect).to_have_been_called_times(2)
  expect(mock_wlan.isconnected).to_have_been_called_times(3)

@test
async def it_should_trigger_the_disconnected_event_on_connection_loss():
  (wlan, mock_wlan) = default_wlan_harness()
  disconnect_observer = observe(wlan.on_disconnected)
  mock_wlan.status.returns(network.STAT_CONNECTING)
  mock_wlan.isconnected.define_returns(True, False)

  await wlan.connect()
  await disconnect_observer.wait()

  expect(disconnect_observer).to_have_been_triggered()

@test
async def it_should_trigger_the_connected_event_on_reconnection():
  (wlan, mock_wlan) = default_wlan_harness()
  mock_wlan.status.returns(network.STAT_CONNECTING)
  mock_wlan.isconnected.define_returns(True, True)
  mock_wlan.isconnected.returns(False)

  await wlan.connect()
  await uasyncio.sleep(3)
  wlan.on_connected.clear()
  reconnected_observer = observe(wlan.on_connected)
  mock_wlan.isconnected.define_returns(True) # Simulate reconnect
  await reconnected_observer.wait()

  expect(reconnected_observer).to_have_been_triggered()

@test
async def it_should_return_the_connection_status():
  (wlan, mock_wlan) = default_wlan_harness()  
  mock_wlan.isconnected.define_returns(True, False)

  expect(wlan.is_connected()).to_be(True)
  expect(wlan.is_connected()).to_be(False)

@test
async def it_should_get_the_mac_address():
  (wlan, mock_wlan) = default_wlan_harness()

  mock_wlan.config.returns(b'\x00\x11\x22\x33\x44\x55')

  expect(wlan.get_mac_address()).to_be('00:11:22:33:44:55')

@test
async def it_should_get_the_ip_address():
  (wlan, mock_wlan) = default_wlan_harness()

  mock_wlan.ifconfig.returns(['192.168.1.123', '255.255.255.0', '192.168.1.1', '192.168.1.1'])

  expect(wlan.get_ip_address()).to_be('192.168.1.123')

@test
async def it_should_disconnect_the_wlan_interface():
  (wlan, mock_wlan) = default_wlan_harness()

  wlan.disconnect()

  expect(mock_wlan.disconnect).to_have_been_called()
  expect(mock_wlan.active).to_have_been_called_with(False)

@test
async def it_should_trigger_the_on_disconnected_event_on_manual_disconnect():
  (wlan, _) = default_wlan_harness()
  observer = observe(wlan.on_disconnected)

  wlan.disconnect()
  await observer.wait()

  expect(observer).to_have_been_triggered()

def default_wlan_harness():
  mock_wlan = MockWlan()
  wlan = Wlan(ssid = 'ssid', password = 'pass', wlan = mock_wlan)
  mock_wlan.isconnected.returns(False)
  return (wlan, mock_wlan)

run()