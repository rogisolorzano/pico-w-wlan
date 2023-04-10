import ubinascii
import uasyncio
import network

class InvalidPasswordException(Exception):
  pass

class AccessPointUnreachableException(Exception):
  pass

class ConnectionFailedException(Exception):
  pass

class TimeoutException(Exception):
  pass

# Connected to WLAN, but have not gotten an IP address yet. It could take a couple seconds for
# an IP address to be assigned after connecting. This is missing in the 'network.STAT_*' codes.
STAT_NO_IP = 2

FAILURE_CODE_EXCEPTIONS = {
  network.STAT_WRONG_PASSWORD: lambda : InvalidPasswordException("Invalid password was provided."),
  network.STAT_NO_AP_FOUND: lambda : AccessPointUnreachableException("Access point is not reachable."),
  network.STAT_CONNECT_FAIL: lambda : ConnectionFailedException("The connection failed for unknown reasons."),
}

class Wlan:
  def __init__(
    self,
    ssid: str,
    password: str,
    timeout: int = 30,
    retry_count: int = 3,
    debug: bool = False,
    wlan = network.WLAN(network.STA_IF),
  ) -> None:
    self._wlan = wlan
    self._ssid = ssid
    self._password = password
    self._timeout = timeout
    self._retry_count = retry_count
    self._debug = debug
    self._should_stay_connected = False
    self._attempting_reconnect = False
    self.on_connected = uasyncio.Event()
    self.on_disconnected = uasyncio.Event()

  async def connect(self) -> None:
    self._wlan.active(True)
    # Disable power-saving mode for better connectivity.
    self._wlan.config(pm = 0xA11140)
    current_attempt = 1

    while (current_attempt <= self._retry_count):
      try:
        self._print('Trying to connect. Attempt #{}'.format(current_attempt))
        await self._connect()
        break
      except InvalidPasswordException:
        raise
      except Exception as err:
        self._print(err)
        if current_attempt == self._retry_count:
          self._print('Failed to connect to the network after {} attempts.'.format(self._retry_count))
          raise
        current_attempt += 1

    self._print('Successfully connected to the network.')
    self._should_stay_connected = True
    uasyncio.create_task(self._maintain_connection())

  def is_connected(self) -> bool:
    return self._wlan.isconnected()

  def disconnect(self) -> None:
    self._should_stay_connected = False
    self._wlan.disconnect()
    self._wlan.active(False)
    self.on_disconnected.set()

  def get_mac_address(self) -> str:
    return ubinascii.hexlify(self._wlan.config('mac'), ':').decode()

  def get_ip_address(self) -> str:
    return self._wlan.ifconfig()[0]

  async def _connect(self):
    self._wlan.connect(self._ssid, self._password)

    for _ in range(self._timeout):
      await uasyncio.sleep(1)

      if self._wlan.isconnected():
        break

      status = self._wlan.status()

      if status == network.STAT_CONNECTING or status == STAT_NO_IP:
        continue

      if not status in FAILURE_CODE_EXCEPTIONS:
        raise OSError("Connection failed. Unexpected status code received: {}".format(status))

      raise FAILURE_CODE_EXCEPTIONS[status]()
    else:
      self._wlan.disconnect()
      raise TimeoutException("Connection timed out.")

    self._attempting_reconnect = False
    self.on_connected.set()

  async def _maintain_connection(self):
    while self._should_stay_connected:
      await uasyncio.sleep(1)

      if self._wlan.isconnected():
        continue

      if not self._attempting_reconnect:
        self._print('Connection lost. Trying to re-connect.')
        self._attempting_reconnect = True
        self.on_disconnected.set()

      try:
        await self._connect()
        self._print('Connection re-established.')
      except Exception as err:
        self._print(err)
        self._print('Could not re-connect. Trying again.')

  def _print(self, message):
    if self._debug:
      print(message)