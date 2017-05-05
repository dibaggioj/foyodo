# FoYoDo

https://foyodo.bitbucket.io

## Authors
Nanu Ahluwalia  
John DiBaggio  
Kyle Etsler  

## Description
This is the FoYoDo embedded project for Raspberry Pi

## Hardware
- Raspberry Pi B+ (or newer)  
- Raspberry Picamera  
- 5V-12V PIR Motion Sensor  
- Dymo M10 USB scale  
- SPDT Switch  
- LEDs (and resistors)  

## Included libraries/projects
- libusb1  
- numpy   
- picamera  
- pyusb  
- RPi  
- twilio   
- youtube-upload  (https://github.com/tokland/youtube-upload)  

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