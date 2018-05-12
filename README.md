# sugardl - A tool to automate downloading all files from your SugarSync account
https://github.com/RamseyK/sugardl


Python script to automate the bulk download of all files in your SugarSync account using SugarSync Developer APIs

## Usage:

```bash
main.py -u <SUGARSYNC USERNAME> -p <SUGARSYNC PASSWORD> -a <APPID> -publicAccessKey <ACCESS KEY> -privateAccessKey <PRIVATE ACCESS KEY> -o "/Users/jsmith/output"

```


```bash
usage: main.py [-h] -u USER -p PASSWORD -a APPID -publicAccessKey
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

* Python 3.5+ or Python 2.7 (untested)
* [requests](https://pypi.python.org/pypi/requests)
* [python-dateutil](https://pypi.org/project/python-dateutil/)

## License:
See LICENSE.txt
