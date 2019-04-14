# Husky Plugin

#### Version 1.0.0

Interface to Husqvarna Automower(R)

## Change history

Inital version

## Requirements

A valid Husqvarna account you can login with userid and password.
To get this account, use the Husqvarna AMC App on your smartphone.
You should have this app working in order to use this plugin.

### Needed software

no special Python modules needed until now. 

### Supported Hardware

In gerneral, all Automower models should be supported.

## Configuration

### plugin.yaml

Please refer to the documentation generated from plugin.yaml metadata.

````yaml
am315x:
    class_name: Husky
    class_path: plugins.husky
    userid: email@domain.de 
    password: mysecret 
```

### items.yaml

Please refer to the documentation generated from plugin.yaml metadata.


## Methods
Please refer to the documentation generated from plugin.yaml metadata.


## Examples



# Credits to

* SmartHome NG Team
* Christophe Carré ([@crisz](https://github.com/chrisz) and his [pyhusmow](https://github.com/chrisz/pyhusmow) project)
* David Karlsson ([@dinmammas](https://github.com/dinmammas) and his [homebridge-robonect](https://github.com/dinmammas/homebridge-robonect) project)
* Jake Forrester ([@rannmann](https://github.com/rannmann) and his [node-husqvarna-automower](https://github.com/rannmann/node-husqvarna-automower) project)
* NextDom Team ([@NextDom](https://github.com/NextDom) and his [plugin-husqvarna](https://github.com/NextDom/plugin-husqvarna) project)

