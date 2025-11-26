import random
import re
import time
from threading import Thread
import requests
import subprocess
import sys
import os
# url = "http://127.0.0.1:9008/jsonrpc/0"
url = "http://192.168.25.22:9008/jsonrpc/0"




headers = {
    'User-Agent': 'uiautomator2',
    'Accept-Encoding': '',
    'Content-Type': 'application/json'
}

json_data = {"jsonrpc": "2.0", "id": 1, "method": "takeScreenshot", "params": [1, 80]}
response = requests.post(
    url, headers=headers, json=json_data
)
print(response.text.rstrip())
