# Infra-Red Imaging Software

## Description

IRIS (Infra-Red Imaging Software) is a suite of camera firmware and imaging processing functions
for interfacing with multiple hardware options.

## Introduction


## Installation Instructions

1. In terminal navigate to Folder location for installation
2. Create virtual environment in terminal:
    >Linux   : python3 -m venv .venv </br>
    Windows : python -m venv .venv
3. Activate virtual environment using:
   >cd .venv/Scripts
   > ./activate
4. Install python requirements.txt through proxy server:
    >pip install --proxy http://ProxyServerIP:Port -r requirements.txt
5. If any packages are missing, then install python packages through proxy server: 
    >pip install --proxy http://ProxyServerIP:Port {python package name}
6. Run Script
    >python.exe {Script Address}