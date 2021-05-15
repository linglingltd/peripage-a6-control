# peripage-a6-control
Python module to control the PeriPage A6-printer via bluetooth.
This script has successfully been tested using a raspberry PI 4.

## What does it support?
This module allows printing of ASCII-Text, Images and SVG vector images.

## How to use it?
Just include the module into your own project and you can start.
An example script (e.g. for testing your setup and as an inspiration) can be found in ppa6test.py.

## Where do these Hex-values come from?
These values have been found out by reverse engineering the communication of the printer and a smartphone.
This has been done by Elias Weingaertner, so check out his project [Peripage A6 CommandLine-Tool](https://github.com/eliasweingaertner/peripage-A6-bluetooth) for futher details.