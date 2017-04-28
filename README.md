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

## /config.json schema

```
{
  "twilio": {
    "account": {String},
    "token": {String},
    "phone": {String}
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

## /youtube.json schema

```
{
    "installed": {
        "auth_provider_x509_cert_url": {String},
        "auth_uri": {String},
        "client_id": {String},
        "client_secret": {String},
        "playlist_id": {String},
        "playlist_name": {String},
        "project_id": {String},
        "redirect_uris": [{String}, {String}],
        "token_uri": {String}
    }
}
```