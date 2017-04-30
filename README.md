# FoYoDo

## Authors
Nanu Ahluwalia  
John DiBaggio  
Kyle Etsler  

## Description
This is the FoYoDo embedded project for Raspberry Pi

## Hardware
- Raspberry Pi B+ (or newer)  
- Raspberry Camera  
- Dymo M10 USB scale  
- HC-SR04 Ultrasonic Sensor  

## /foyodo/config.json schema

```
{
  "twilio": {
    "account": {String},
    "token": {String},
    "phone": {String}
  },
  "youtube": {
    "playlist_id": {String},
    "playlist_name": {String}
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

## /foyodo/youtube_client.json, /foyodo/lib/youtube-upload-master/client_secrets.json schema

```
{
    "installed": {
        "auth_provider_x509_cert_url": {String},
        "auth_uri": {String},
        "client_id": {String},
        "client_secret": {String},
        "project_id": {String},
        "redirect_uris": [{String}, {String}],
        "token_uri": {String}
    }
}
```