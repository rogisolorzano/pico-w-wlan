from microtest import spy

class MockNetwork:
  def __init__(self):
    self.STAT_CONNECTING = 1
    self.STAT_CONNECT_FAIL = -1
    self.STAT_NO_AP_FOUND = -2
    self.STAT_WRONG_PASSWORD = -3
    self.STA_IF = 0
    self.WLAN = spy()