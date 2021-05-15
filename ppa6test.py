#!/usr/bin/env python3

"""
Simple test procedure for manual printing functions of ppa6ctl module
"""

import ppa6ctl as printer

print("Start module ppa6ctl test procedure")

print("Search for a PeriPage printer, this might take some time...")
mac = printer.search()

if not mac:
  print("No printer found, stopping test procedure")
  exit()

print("Connecting to: %s" % mac)
if not printer.connect(mac):
  print("Connection to printer failed, stopping test procedure")
  print("Error:", printer.getLastError())

print("Is printer connected? %s" % "Yes" if printer.connected() else "No")
print("Device name: %s" % printer.getDeviceName())
print("Device Firmware and DPI: %s" % printer.getFWDPI())
print("Device serial: %s" % printer.getSerial())

print("Start printing...")
printer.printStart()

print("Print line: 'ppa6ctl test procedure")
printer.printLn("ppa6ctl test procedure")

print("Print device name")
printer.printString("Device name: ")
printer.printLn(printer.getDeviceName())

print("Print FW and DPI")
printer.printString("FWDPI: ")
printer.printLn(printer.getFWDPI())

print("Print serial")
printer.printString("Serial: ")
printer.printLn(printer.getSerial())

print("Print black line, 1px")
printer.printFeed(1, False)

print("Print white line, 1px")
printer.printFeed(1, True)

print("Print black line, 1px")
printer.printFeed(1, False)

print("Print image: test.jpg, enhance brightness by 1.5, contrast by 0.75")
printer.printImage("test.jpg", 1.5, 0.75)

print("Print white line, 20px")
printer.printFeed(20)

print("Print line: 'Visit: www.elektronikundco.de")
printer.printLn("Visit: www.elektronikundco.de")

print("Print QR code: 'www.elektronikundco.de'")
printer.printQR("www.elektronikundco.de")

print("Print SVG: logo.svg")
printer.printImage("logo.svg")

print("Stop printing...")
printer.printStop()

print("Disconnecting")
printer.disconnect()

error = printer.getLastError()
if error:
  print("An error occured during test procedure:", error)

print("End module ppa6ctl test procedure")
