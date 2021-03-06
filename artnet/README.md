# Artnet

## Requirements

You need a device understanding Artnet.
I suggest to use the software OLA http://www.opendmx.net/index.php/Open_Lighting_Architecture to translate the ArtNet packets into DMX Signals.
OLA supports most USB -> DMX Adapters available at the moment.

## Supported Hardware

* Hardware supported by OLA. See Link above.

## Configuration

### plugin.yaml

```
dmx1:
	class_name: ArtNet
	class_path: plugins.artnet
	artnet_subnet: 0
	artnet_net: 0
	artnet_universe: 0
	ip: 192.168.1.123
	port: 6454
```

### items.yaml

Not needed yet.

### logic.yaml
Notice: First DMX channel is 1! Not 0!

To send DMX Data to the universe set in plugin.yaml you have 3 possibilities:

#### 1) Send single value
``sh.dmx1(<DMX_CHAN>, <DMX_VALUE>)``

Sets DMX_CHAN to value DMX_VALUE.

Example: ``sh.dmx1(12,255)``
If channels 1-11 are already set, they will not change.
If channels 1-11 are not set till now, the will be set to value 0.
This is needed because on a DMX bus you can not set just one specific channel.
You have to begin at first channel setting your values.

#### 2) Send a list of values starting at channel
``sh.dmx1(<DMX_CHAN>, <DMX_VALUE_LIST>)``
Sends <DMX_VALUE_LIST> to DMX Bus starting at <DMX_CHAN>

Example:
``sh.dmx1(10,[0,33,44,55,99])``
If channels 1-9 are already set, they will not change.
If channels 1-9 are not set till now, the will be set to value 0.
This is needed because on a DMX bus you can not set just one specific channel.
You have to begin at first channel setting your values.
Values in square brackets will be written to channel (10-14)

#### 3) Send a list of values

``sh.dmx1(<DMX_VALUE_LIST>)``

Sends <DMX_VALUE_LIST> to DMX Bus starting at channel 1

This is nearly the same as 2) but without starting channel.

Example:

``sh.dmx1([0,33,44,55,99])``
Values in Square brackets will be written to channel (1-5)
