'''
  name:         ppa6ctl
  description:  Python module to control PeriPage A6 printer
  author:       Kevin Mader, Alexander Weigl
  website:      https://www.elektronikundco.de
  git:          https://github.com/linglingltd/peripage-a6-control

  Credits to Elias Weingaertner
  for reverse engineering the protocol
  https://github.com/eliasweingaertner/peripage-A6-bluetooth
  
  Tested with PeriPage A6, 203dpi
  https://peripagepocketprinter.com/collections/pocket-printers/products/pocket-printer?variant=32420578394163
  Horizontal resolution: 384px
  Turns itself off after 20min of no bluetooth communication
'''

import os
import re
import time
import qrcode
import threading
import bluetooth
from io import BytesIO
from cairosvg import svg2png
from PIL import Image, ImageOps, ImageEnhance


_address = None # format: 00:00:00:00:00:00
_sock = None
_lastError = ""
_printing = False
_keepAliveThread = None


# Connection management and basic control
def search(name = "PeriPage"):
  '''Searches nearby bluetooth devices for a PeriPage printer and returns its MAC address'''
  devices = bluetooth.discover_devices(lookup_names = True)

  for address, devname in devices:
    if devname.find(name) != -1:
      return address

  return False


def connect(address, keepalive = False):
  '''Connects to a given address using Bluetooth and starts a keepalive thread if wanted'''
  global _address, _sock, _keepAliveThread
  
  # check if address is a valid MAC address
  if not re.fullmatch(r"(([0-9a-f]){2}:){5}([0-9a-f]){2}", address, re.IGNORECASE):
    return error("Invalid MAC address, format: 00:00:00:00:00:00")

  _address = address
  _sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
  
  try:
    _sock.connect((_address, 1))
  except:
    return error("BluetoothSocket connection failed")
  
  reset()
  
  if keepalive:
    _keepAliveThread = threading.Thread(target=_keepaliveFunc)
    _keepAliveThread.start()

  return True


def connected():
  '''Returns the connection status'''
  global _address, _sock

  try:
    _sock.getpeername()
    return True
  except:
    return False


def disconnect():
  '''Close the connection to the Bluetooth printer'''
  global _sock
  
  if not _sock:
    return error("Printer not connected")
  
  _sock.close()
  _sock = None
  
  return True


def _keepaliveFunc():
  '''Periodically gets the device name of the printer to prevent printer shutdown'''
  global _keepAliveThread, _printing
  
  count = 60
  
  while True:
    # Only force communication if nothing is printed now
    if not _printing:
      if not connected():
        break
        
      if count == 0:
        count = 60

        if not getDeviceName():
          break

      if count > 0:
        count = count - 1

    time.sleep(1)
    
  _keepAliveThread = None


def reset():
  global _sock
  
  if not _sock:
    return error("Printer not connected")

  _sock.send(bytes.fromhex("10ff50f1"))
  data = _sock.recv(32)
  _sock.send(bytes.fromhex("000000000000000000000000"))
  return data


def reset2():
  global _sock

  if not _sock:
    return error("Printer not connected")

  sock.send(bytes.fromhex("10ff100002"))
  data = sock.recv(32)
  return data


def getDeviceName():
  '''Returns the printers device name'''
  global _sock
  
  if not _sock:
    return error("Printer not connected")

  _sock.send(bytes.fromhex("10ff3011"))
  data = _sock.recv(32)
  
  try:
    decoded = data.decode("ascii")
    return decoded
  except:
    return False

def getFWDPI():
  '''Returns the printers firmware and dpi'''
  global _sock
  
  if not _sock:
    return error("Printer not connected")
  
  _sock.send(bytes.fromhex("10ff20f1"))
  data = _sock.recv(32)
  
  try:
    decoded = data.decode("ascii")
    return decoded
  except:
    return False


def getSerial():
  '''Returns the printers serial number'''
  global _sock
  
  if not _sock:
    return error("Printer not connected")

  _sock.send(bytes.fromhex("10ff20f2"))
  data = _sock.recv(32)
  
  try:
    decoded = data.decode("ascii")
    return decoded
  except:
    return False



# Error functions
def getLastError():
  '''Returns the last error message and clears the buffer'''
  global _lastError
  
  errorMessage = _lastError
  _lastError = ""
  return errorMessage

def error(message):
  '''Writes an error message to the buffer'''
  global _lastError
  _lastError = message
  return False
  
  
  
# Automatic printing
def image(filename, brightness = 0, contrast = 0):
  '''Prints an image'''
  if not printStart():
    return False
    
  if not printImage(filename, brightness, contrast):
    return False
    
  return printStop()
  
def QR(data):
  '''Prints QR code'''
  if not printStart():
    return False
  if not _printImage(qrcode.make(data)):
    return False

  return printStop()

def text(text):
  '''Prints some text'''
  if not printStart():
    return False
    
  if not printLn(text):
    return False
    
  return printStop()
  
def feed():
  '''Feeds some paper'''
  if not printStart():
    return False
    
  return printStop()



# Manual printing
def printStart():
  '''Starts manual printing mode'''
  global _sock, _printing
  
  if not _sock:
    return error("Printer not connected")
  
  _printing = True

  _sock.send(bytes.fromhex("10fffe01"))
  
  return True


def printStop():
  '''Stops manual printing mode and feed paper for a clean cut'''
  global _sock, _printing
  
  if not _sock:
    return error("Printer not connected")
  
  _sock.send(bytes.fromhex("1b4a4010fffe45"))
  
  # Get answer code, \xAA seems to be printed successfully
  data = _sock.recv(32)

  _printing = False
  
  return True


def printString(text):
  '''Prints a string in manual printing mode'''
  global _sock
  
  if not _sock:
    return error("Printer not connected")
  
  # Remove non ASCII characters
  outputString = re.sub(r'[^\x00-\x7F]+','?', text) # maybe compile the regex?
  
  line = bytes(outputString, "ascii")
  _sock.send(line)
  
  return True


def printNewline():
  '''Prints a newline in manual printing mode'''
  return printString("\n")


def printLn(text):
  '''Prints a line in manual printing mode'''
  if not printString(text):
    return False
    
  return printNewline()


def printFeed(lines, blank = True):
  '''Feeds paper on pixel basis, white or black in manual printing mode'''
  if lines > 65535:
    return error("Too much lines, maximum: 65535")

  global _sock
  
  if not _sock:
    return error("Printer not connected")
  
  height_bytes = (lines).to_bytes(2, byteorder = "little")
  _sock.send(bytes.fromhex("1d7630003000") + height_bytes)
  
  line = [(0 if blank else 255) for i in range(0, 48)]

  for i in range(0, lines):
    _sock.send(bytes(line))
    time.sleep(0.02)
    
  return True

def printQR(data):
  '''Prints QR code in manual printing mode'''
  return _printImage(qrcode.make(data))


def printImage(filename, brightness = 0, contrast = 0):
  '''Prints an image file in manual printing mode'''
  file_name, file_extension = os.path.splitext(filename)

  img = None

  if file_extension == '.svg':
    png_data = svg2png(file_obj=open(filename, "rb"), background_color = "#FFFFFF", output_width = 384)
    img = Image.open(BytesIO(png_data))
  else:
    img = Image.open(filename)
  
  return _printImage(img, brightness, contrast)


def _printImage(img, brightness = 0, contrast = 0):
  '''Prints an image object in manual printing mode'''
  global _sock
  
  if not _sock:
    return error("Printer not connected")
  
  # make image greyscale
  img = img.convert("L")

  img_width = img.size[0]
  img_height = img.size[1]

  # brightness / contrast
  if brightness:
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness)

  if contrast:
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)

  img = ImageOps.invert(img)

  new_width = 384 #Peripage A6 image width
  scale = new_width / float(img_width)
  new_height = int(img_height * scale)

  if new_height > 65535:
    return error("Image height too big, maximum supported: 65535")

  img = img.resize((384, new_height), Image.ANTIALIAS)

  # make image b/w
  img = img.convert("1")

  height_bytes = new_height.to_bytes(2, byteorder = "little")
  _sock.send(bytes.fromhex("1d7630003000") + height_bytes)

  # send image to printer, line by line
  image_bytes = img.tobytes()

  # a chunk is one line, 48byte * 8 = 384bit
  chunksize = 48
  for i in range(0, len(image_bytes), chunksize):
    chunk = image_bytes[i:i + chunksize]
    _sock.send(chunk)
    time.sleep(0.02)
    
  return True
