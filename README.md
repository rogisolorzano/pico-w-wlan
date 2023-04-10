# Pico W Wlan

An async WLAN module for the Raspberry Pi Pico W. This module handles the edge cases around reliably
connecting to WLAN and maintaining that connection over time. It also provides connected and disconnected
events you can hook into.

## Usage

Just copy `wlan.py` over to wherever you're using it.

Initialize the Wlan class

```
wlan = Wlan(ssid = 'Hogwarts', password = 'MyPassword')
```

Call connect
```
await wlan.connect()
```

## Configuration

These are the configuration options:

| Name  | Required | Default | Description |
| ----- | -------- | ------- | ----------- |
| ssid | yes | None | The SSID |
| password | yes | None | The password |
| timeout | no | 30 | The amount of seconds to wait for the initial connection to be made |
| retry_count | no | 3 | The amount of times to retry connecting. This is for the initial connection. After the initial connection has been made, we retry indefinitely until we are re-connected. |
| debug | no | False | Whether to print helpful debug messages. |
| wlan | no | network.WLAN(network.STA_IF) | Override the wlan interface used under the hood. |

Example initializing Wlan with other options:

```
wlan = Wlan(
  ssid = 'Hogwarts',
  password = 'MyPassword',
  retry_count = 5,
  debug = True
)
```

## Lifecycle events
This module uses `uasyncio.Event()` to signal connected and disconnected events. You can use these to
start/stop tasks, subscribe to topics, pause/resume consumption of a queue, etc.

Create the functions that will handle these events:
```
async def on_connect(wlan):
  while True:
    await wlan.on_connected.wait()
    wlan.on_connected.clear()
    print('Handling the on_connnected event.')
    print('MAC address', wlan.get_mac_address())
    print('IP address', wlan.get_ip_address())
    # Do stuff

async def on_disconnect(wlan):
  while True:
    await wlan.on_disconnected.wait()
    wlan.on_disconnected.clear()
    print('Handling the on_disconnected event.')
    # Do stuff
```

Use `uasyncio` to create these tasks:
```
for coroutine in (on_connect, on_disconnect):
  uasyncio.create_task(coroutine(wlan))
```

## Full example

```
from wlan import Wlan
import uasyncio

async def on_connect(wlan):
  while True:
    await wlan.on_connected.wait()
    wlan.on_connected.clear()
    print('Handling the on_connnected event.')
    print('MAC address', wlan.get_mac_address())
    print('IP address', wlan.get_ip_address())

async def on_disconnect(wlan):
  while True:
    await wlan.on_disconnected.wait()
    wlan.on_disconnected.clear()
    print('Handling the on_disconnected event.')

wlan = Wlan(ssid = 'Hogwarts', password = 'MyPassword')

async def main(wlan: Wlan):
  await wlan.connect()

  for coroutine in (on_connect, on_disconnect):
    uasyncio.create_task(coroutine(wlan))

  while True:
    await uasyncio.sleep(15)

try:
  uasyncio.run(main(wlan))
finally:
  wlan.disconnect()
  uasyncio.new_event_loop()
```
