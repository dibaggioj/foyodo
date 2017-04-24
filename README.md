# FoYoDo

## Authors
Nanu Ahluwalia
John DiBaggio
Kyle Etsler

## Hardware
- Raspberry Pi B+ (or newer)
- Raspberry Camera
- Dymo M10 USB scale
- HC-SR04 Ultrasonic Sensor

## config.json schema

```
{
  "twilio": {
    "account": {String},
    "token": {String},
    "phone": {String}
  },
  "youtube": {
    "playlist_name": {String},
    "playlist_id": {String}
  },
  "users": [
    {
      "first_name": {String},
      "last_name": {String},
      "phone": {String}
    },
    ...
  ]
}
```