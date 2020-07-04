from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp
import pandas as pd
from dateutil import tz
from geopy.geocoders import Nominatim
from geopy.location import Location
from pyshorteners import Shortener
from timezonefinder import TimezoneFinder

from config import BITLY_TOKEN, MAPQUEST_API_KEY, N2YO_API_KEY

# suppress a 'caveat' by pandas
pd.set_option('mode.chained_assignment', None)


# these suite of function convert heavens-above data from UTC to local time
def swap_tz(time_utc: datetime, lat: float, lon: float) -> datetime:
    from_zone = tz.gettz('UTC')
    tf = TimezoneFinder()
    to_zone = tz.gettz(tf.timezone_at(lng=lon, lat=lat))
    time_utc = time_utc.replace(tzinfo=from_zone)
    time_local = time_utc.astimezone(to_zone)

    return time_local


def time_convert(dateframe_col: List[str], timeframe_col: List[str],
                 lat: float, lon: float,
                 modify_date: bool = False) -> Tuple[List[str], List[str]]:
    for ii in range(len(dateframe_col)):
        # get the values
        date_cell = dateframe_col[ii]
        time_cell = timeframe_col[ii]

        # create datetime object
        time = datetime.strptime(date_cell + time_cell, '%d %b%H:%M:%S')

        # convert to local time
        time_loc = swap_tz(time, lat, lon)

        # create new datestring and timestring, pop back in
        datestring = time_loc.strftime('%d %b')
        timestring = time_loc.strftime('%H:%M:%S')

        if modify_date is True:
            dateframe_col[ii] = datestring
        timeframe_col[ii] = timestring

    return dateframe_col, timeframe_col


def convert_columns(df: pd.DataFrame, lat: float, lon: float) -> pd.DataFrame:
    date = df[('Date', 'Date')]
    start = df[('Start', 'Time')]
    high = df[('Highest point', 'Time')]
    end = df[('End', 'Time')]

    # convert each
    date_use, start = time_convert(date, start, lat, lon)
    _, high = time_convert(date, high, lat, lon)
    _, end = time_convert(date, end, lat, lon, modify_date=True)

    # replace in dataframe
    df[('Date', 'Date')] = date_use
    df[('Start', 'Time')] = start
    df[('Highest point', 'Time')] = high
    df[('End', 'Time')] = end

    return df


# this is needed for coverting n2yo times
def localtime(unix_time: int, lat: float, lon: float) -> str:
    time_utc = datetime.utcfromtimestamp(unix_time)
    t = swap_tz(time_utc, lat, lon)
    time_string = '%04d-%02d-%02d | %02d:%02d:%02d' % (t.year, t.month, t.day, t.hour, t.minute, t.second)

    return time_string


def where_are_you(location: str) -> Optional[Location]:
    """ input: string (location search)
       output: Nominatim object"""

    geolocator = Nominatim(user_agent='crimsoBOT/astronomy')
    return geolocator.geocode(location)


async def get_iss_loc(query: str, source: str = 'ha') -> Tuple[float, float, str, str]:
    location = where_are_you(query)

    if not location:
        return 0.0, 0.0, 'Location not found!', ''

    lat = round(location.latitude, 4)
    lon = round(location.longitude, 4)

    if source == 'n2yo':
        # code for n2yo (magnitude seems to be underesimated)
        api = N2YO_API_KEY  # n2yo api, append to URL
        url = 'http://www.n2yo.com/rest/v1/satellite/visualpasses/25544/{}/{}/0/10/180/&apiKey={}'.format(lat, lon, api)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                pass_info = await response.json()

        pass_str = (
            '{s} rises in {startAzCompass} · '
            '{p} peaks in {maxAzCompass}({maxEl}°) · '
            '{e} sets in {endAzCompass} · '
            'Mag: {pl}{mag}'
        )

        pass_list = []
        try:
            for event in pass_info['passes']:
                if float(event['maxEl']) < 15:
                    continue

                # convert unix to local
                start = localtime(event['startUTC'], lat, lon)
                peak = localtime(event['maxUTC'], lat, lon)[13:]
                end = localtime(event['endUTC'], lat, lon)[13:]

                # formatting cardinal directions
                event['startAzCompass'] += (3 - len(event['startAzCompass'])) * ' '
                event['maxAzCompass'] += (3 - len(event['maxAzCompass'])) * ' '
                event['endAzCompass'] += (3 - len(event['endAzCompass'])) * ' '

                # format elevation and mag
                event['maxEl'] = format(float(event['maxEl']), '2.0f')
                plus = ''
                if event['mag'] >= -0.05:
                    plus = ' '
                event['mag'] = format(float(event['mag']), '1.1f')

                # and finally, the string
                pass_list.append(pass_str.format(s=start, p=peak, e=end, pl=plus, **event))
        except Exception:
            pass

        if not pass_list:
            pass_list = ['No passes in the next 10 days!']

        # list of strings to string
        passes = '\n'.join(pass_list)

    if source == 'ha':
        # heavens-above code(gives results in UTC; not easy to parse out either)
        url = 'https://www.heavens-above.com/PassSummary.aspx?satid=25544&lat={}&lng={}'.format(lat, lon)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        dataframe_list = pd.read_html(html)

        # this part contains the table if there is one
        try:
            dataframe = convert_columns(dataframe_list[4], lat, lon)
            if dataframe.empty:
                raise Exception
            else:
                # a few final formatting considerations
                passes = dataframe.to_string()\
                    .replace('Â', ' ')\
                    .replace(' °', '° ')\
                    .replace('Date', '    ', 1)\
                    .replace('Pass type', '         ', 1)
        except Exception:
            passes = 'No passes for the next ten days!'

    return lat, lon, passes, url


def whereis(query: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    # Nomanatim geocoder
    location = where_are_you(query)

    # return None if no location found
    if not location:
        return None, None, None

    lat = round(location.latitude, 6)
    lon = round(location.longitude, 6)

    # get bounding box from raw dict
    bounding = location.raw['boundingbox']

    # get difference btw center and bounding box, and stretch (more if close, less if far)
    dlat = (lat - float(bounding[0]))
    stretch = 10 / dlat ** 0.3
    dlat = (lat - float(bounding[0])) * stretch
    dlon = (lon - float(bounding[2])) * stretch

    # new bounding box
    bound = [lat - dlat, lat + dlat, lon - dlon, lon + dlon]

    # now the URL!
    url_template = (
        'https://www.mapquestapi.com/staticmap/v5/map?'
        'locations={},{}&boundingbox={},{},{},{}&type=dark&size=800,600@2x&key={}'
    )
    url = url_template.format(
        lat, lon,
        bound[0], bound[2], bound[1], bound[3],
        MAPQUEST_API_KEY
    )

    # return url
    # bit.ly shortner
    shortener = Shortener(api_key=BITLY_TOKEN)
    short_url = shortener.bitly.short(url)  # type: str

    return lat, lon, short_url
