import json
import requests
import time
import datetime
import sys
from bs4 import BeautifulSoup
import statistics


def get_market_data():
  # Make request to epexspot, who says I can use the data for "internal use" if it's non-commercial
  r = requests.get("https://www.epexspot.com/en/market-data?market_area=GB&trading_date=" + str(datetime.datetime.now().date()) + "&delivery_date=" + str((datetime.datetime.now()+datetime.timedelta(days=1)).date()) + "&underlying_year=&modality=Auction&sub_modality=DayAhead&product=60&data_mode=table&period=")

  # If you ask for the data too early, the website seems to return data for a different day. Look for a H2 tag which lists the day which has been returned, search for the day of month we're searching for. If it's there then we're good to go
  # To an extent this can be mitigated by not asking for the auction results before middday
  h2 = BeautifulSoup(r.text, 'html.parser').find_all('h2')
  if len(h2) > 0 and str(h2[0]).find(str((datetime.datetime.now()+datetime.timedelta(days=1)).day)) < 0:
    raise RuntimeError("Data not ready yet - Page not rendered")
  else:
    # Take HTML from request, find <td> tags, starting with the 4th entry (zero index) and skipping 4 after that. This should be the price
    numbers = BeautifulSoup(r.text, 'html.parser').find_all('td')[3::4]
    
    # Convert these BS4 tags to a string, splice them to remove <td></td> tags, and then cast the result as a float
    numbers = list(map(lambda e : float(str(e)[4:-5]), numbers))
    #print(len(numbers))
    if len(numbers)>0:
      # Then we want the mean. This is in £/gW, we want p/kW, so *0.1
      wholesale_day_price = statistics.mean(numbers)*0.1

      # Now calculate the Octopus cost. This is hard coded for South East because.. Lazy... And add the VAT at 5%
      retail_price = ((wholesale_day_price * 1.19) + 7.502) * 1.05

      return(retail_price)
    else:
      raise RuntimeError("Data not ready yet - No results")

def get_octopus_data(searchdate, fuel):
  if fuel == "electric":
    r = requests.get("https://octopus.energy/api/v1/tracker/E-1R-SILVER-2017-1-J/monthly/future/12/5320/")
  else:
    r = requests.get("https://octopus.energy/api/v1/tracker/G-1R-SILVER-2017-1-J/monthly/future/12/5320/")

  for period in r.json()["periods"]:
    perioddate = period["date"].split("-")

    if int(perioddate[0]) == searchdate.year and int(perioddate[1]) == searchdate.month:
      return period["breakdown"]["unit_rates"]["raw"][searchdate.day-1]*1.05
      #break


searchdate = datetime.datetime.now()
if sys.argv[2] == "today":
  rate = get_octopus_data(datetime.datetime.now(),sys.argv[1])
else:
  if sys.argv[1] == "gas":
    # Gas seems to vary a lot less
    rate = get_octopus_data(datetime.datetime.now() + datetime.timedelta(days=1),sys.argv[1])
  else:
    # If it's afternoon, we should have market data for tomorrow, which will be much more accurate
    if datetime.datetime.now().hour >= 12:
      try:
        rate = get_market_data()
      except:
        rate = get_octopus_data(datetime.datetime.now() + datetime.timedelta(days=1),sys.argv[1])
    else:
      rate = get_octopus_data(datetime.datetime.now() + datetime.timedelta(days=1),sys.argv[1])

print(round(rate,2))
