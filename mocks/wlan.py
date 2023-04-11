from microtest import spy

class MockWlan:
  def __init__(self):
    self.connect = spy()
    self.disconnect = spy()
    self.status = spy()
    self.active = spy()
    self.isconnected = spy()
    self.config = spy()
    self.ifconfig = spy()