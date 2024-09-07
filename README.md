# SugarDL - A tool to automate downloading all files from your SugarSync account
https://github.com/RamseyK/sugardl


Python script to automate downloading all files in your SugarSync account using SugarSync Developer APIs.  Useful for when you can't install the SugarSync client on your destination machine (ie. Linux), or want to automate backups of your storage.

## Usage:

```bash
sugardl.py -u <SUGARSYNC USERNAME> -p <SUGARSYNC PASSWORD> -a <APPID> -publicAccessKey <ACCESS KEY> -privateAccessKey <PRIVATE ACCESS KEY> -o "/Users/jsmith/output"

```


```bash
usage: sugardl.py [-h] -u USER -p PASSWORD -a APPID -publicAccessKey
               PUBLICACCESSKEY -privateAccessKey PRIVATEACCESSKEY -o OUTPUT

A tool to automate downloading all files from your SugarSync account

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  SugarSync Username/Email
  -p PASSWORD, --password PASSWORD
                        Password
  -a APPID, --appId APPID
                        Developer app ID
  -publicAccessKey PUBLICACCESSKEY, --publicAccessKey PUBLICACCESSKEY
                        Developer Public Access Key
  -privateAccessKey PRIVATEACCESSKEY, --privateAccessKey PRIVATEACCESSKEY
                        Developer Private Access Key
  -o OUTPUT, --output OUTPUT
                        Output directory

```

## Requirements:

### SugarSync

* SugarSync account
* AppId & API Keys from the [SugarSync developer console](https://www.sugarsync.com/developer/account)

### Python

* Python 3.5+
* [requests](https://pypi.python.org/pypi/requests)
* [python-dateutil](https://pypi.org/project/python-dateutil/)

## License:
See LICENSE.txt
