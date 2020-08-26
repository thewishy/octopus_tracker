import json
import requests
import time
import datetime
import sys


searchdate = datetime.datetime.now()

if sys.argv[2] == "tomorrow":
    searchdate = searchdate + datetime.timedelta(days=1)

if sys.argv[1] == "electric":
    r = requests.get("https://octopus.energy/api/v1/tracker/E-1R-SILVER-2017-1-J/monthly/future/12/5320/")
else:
    r = requests.get("https://octopus.energy/api/v1/tracker/G-1R-SILVER-2017-1-J/monthly/future/12/5320/")

for period in r.json()["periods"]:
    perioddate = period["date"].split("-")

    if int(perioddate[0]) == searchdate.year and int(perioddate[1]) == searchdate.month:
        print(round(period["breakdown"]["unit_rates"]["raw"][searchdate.day-1]*1.05,2))
        break
