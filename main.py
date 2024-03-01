# --------------------------------------------------------------------------------- #
#                                                                                   #
#    Project:          RFID Bike Locker                                             #
#    Module:           main.py                                                      #
#    Authors:          VEX (template code                                           #
#                      Rob Poulter (Comms code)                 
#                      Damien Kee (motor control)
#                      Sharon Harrison (mods to suit task)                          #
#    Created:          Fri Aug 05 2022                                              #
#    Description:      RFID connected to Raspberry Pi to trigger unlock/lock        #
#                      Sends signal to VEX IQ, which rotates motor CW to unlock     #
#                      and CCW to lock. TouchLED Red(locked), green(unlocked) and   #
#                      sound alarms each way.                                       #
#                                                                                   #
#    Configuration:                                                                 #
#                      TouchLED in Port 2
#                      Motor on Port 10                                             #
#                                                                                   #
# --------------------------------------------------------------------------------- #


#vex:disable=repl
from vex import *

brain=Brain()

# Robot configuration code
brain_inertial = Inertial()
motor_locker = Motor(Ports.PORT10, 1, True)
motor_locker.set_velocity(20)
touchled_2 = Touchled(Ports.PORT2)
bumper_num1 = Bumper(Ports.PORT7)
bumper_num2 = Bumper(Ports.PORT8)
keycode = ["1", "2", "2", "1"]

try:
    import uasyncio as asyncio
except ImportError:
    try:
        import asyncio
    except ImportError:
        print("asyncio not available")
        raise SystemExit

class SerialMonitor:
  def __init__(self, brain, touchled_2, motor_locker):
    self.serial_port = None
    self.brain = brain
    self.buffer = "" # incoming string buffer
    self.packets = [] # complete packets
    self.read_errors = 0 # exceptions from serial read or decode
    self.encode_errors = 0 # invalid packet encoding
    try:
      self.serial_port = open('/dev/serial1', 'r+b')
    except:
      self.brain.screen.print("Serial port not available")
      raise SystemExit

  async def read_serial(self):
    """
    Constantly read lines from the serial port and add them to the
    buffer. There's some basic error monitoring here, but it seems
    fairly reliable so far at low volumes (tested processing 10 messages
    per second so far without issue)
    """
    while True:
      try:
        line = self.serial_port.readline()
        if line:
          self.buffer += line.decode().strip()
      except:
        self.read_errors += 1
      await asyncio.sleep(0)

  async def report_serial(self):
    """
    Check the contents of the serial buffer to see if any complete
    packets are available, and then process any complete packets.
    """

    while True:
      if len(self.buffer) > 0:
        # check for a complete packet, see if we have an end marker
        b = self.buffer.split(":E", 1)
        if len(b) > 1:
          # if we have a start marker, add the contents to the packets
          # list, log any bad packets to the counter
          if b[0].startswith("M:"):
            self.packets.append(b[0][2:])
          else:
            self.encode_errors += 1
          # reset the buffer to the rest of the string, this should
          # discard any invalid packets
          self.buffer = b[1]

      # If there are any packets on the queue, pop off the first packet
      # and process it. This example prints the x and y coordinates to
      # separate lines on the screen and also controls the two motors
      # to move the camera.
      if len(self.packets) > 0:
        packet = self.packets.pop(0)
        command, allow = packet.split(",")
        self.brain.screen.clear_screen()
        self.brain.screen.set_cursor(1, 1)
        self.brain.screen.print("{}".format(command))
        self.brain.screen.set_cursor(2, 1)
        if allow == "true":
          self.brain.screen.print("Enter code")
          attempts = 0
          self.brain.screen.set_cursor(3, 1)
          nums_pressed = []
          while nums_pressed != keycode and attempts < 3 and len(nums_pressed) < 4:
            if bumper_num1.is_pressed():
              nums_pressed.append("1")
            elif bumper_num2.is_pressed():
              nums_pressed.append("2")
          if nums_pressed != keycode and attempts >= 3:
            self.brain.screen.print("Incorrect code")
            self.brain.screen.set_cursor(4,1)
            self.brain.screen.print("Too many attempts")
            #time.sleep(100)
          else:
            self.brain.screen.print(' '.join(nums_pressed))
            if command == "lock": 
              #self.brain.screen.print("Locking...")
              touchled_2.set_color(Color.RED)
              touchled_2.set_brightness(100)
              motor_locker.spin_for(FORWARD, 60, DEGREES)
              #wait(2000, msec)
            elif command == "unlock" and allow == "true":
              #self.brain.screen.print("Unlocking")
              touchled_2.set_color(Color.GREEN)
              touchled_2.set_brightness(100)
              motor_locker.spin_for(REVERSE, 60, DEGREES)
              #wait(2000, msec)
            else:
              #self.brain.screen.print("ACCESS DENIED!")
              touchled_2.set_color(Color.BLUE)
          brain.play_sound(SoundType.SIREN)


      # give control back to the async loop
      await asyncio.sleep(0)

  def write_serial(self, msg):
    """
    Since we're using serial access over regular file access, probably
    best to flush every time.
    """
    self.serial_port.write("{}\r\n".format(msg).encode("utf-8"))
    self.serial_port.flush()


  def __del__(self):
    self.serial_port.close()


msg = "Starting up..."
brain.screen.print(msg)

# set up the serial monitor and provide it with the VEX objects
monitor = SerialMonitor(brain, touchled_2, motor_locker)

# Set up the async tasks which each run forever - potentially
# add another dummy task with other robot controls and that
# way we get to leave this part of the program alone?
loop = asyncio.get_event_loop()
loop.create_task(monitor.read_serial())
loop.create_task(monitor.report_serial())
loop.run_forever()