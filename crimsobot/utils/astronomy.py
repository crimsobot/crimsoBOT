import ast
from datetime import datetime

import pandas as pd
import requests
from dateutil import tz
from geopy.geocoders import Nominatim
from pyshorteners import Shortener
from timezonefinder import TimezoneFinder

from config import BITLY_TOKEN, MAPQUEST_API_KEY, N2YO_API_KEY

# suppress a 'caveat' by pandas
pd.set_option('mode.chained_assignment', None)


# these suite of function convert heavens-above data from UTC to local time
def swap_tz(time_utc, lat, lon):
    """ input: datetime UTC, latitude (DD, float), longitude (DD, float)
       output: datetime local"""

    from_zone = tz.gettz('UTC')
    tf = TimezoneFinder()
    to_zone = tz.gettz(tf.timezone_at(lng=lon, lat=lat))
    time_utc = time_utc.replace(tzinfo=from_zone)
    time_local = time_utc.astimezone(to_zone)

    return time_local


def swap_month(month_value):
    month_name = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    for key, value in month_name.items():
        if month_value == key:
            return value
        elif month_value == value:
            return key
        else:
            continue


def time_convert(dateframe_col, timeframe_col, lat, lon, modify_date=False):
    year = datetime.now().year
    for ii in range(len(dateframe_col)):
        # get the values
        day = dateframe_col[ii][0:2]
        month = dateframe_col[ii][3:6]
        hh = timeframe_col[ii][0:2]
        mm = timeframe_col[ii][3:5]
        ss = timeframe_col[ii][6:8]

        # create datetime object
        time = datetime(year, swap_month(month), int(day), int(hh), int(mm), int(ss))

        # convert to local time
        time_loc = swap_tz(time, lat, lon)

        # create new datestring and timestring, pop back in
        datestring = '%02d %s' % (time_loc.day, swap_month(time_loc.month))
        timestring = '%02d:%02d:%02d' % (time_loc.hour, time_loc.minute, time_loc.second)
        # print('{} {}'.format(datestring, timestring))

        if modify_date is True:
            dateframe_col[ii] = datestring
        timeframe_col[ii] = timestring

    return dateframe_col, timeframe_col


def convert_columns(df, lat, lon):
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
def localtime(unix_time, lat, lon):
    """ input: unix time UTC (s), latitude (DD, float), longitude (DD, float)
       output: string"""

    time_utc = datetime.utcfromtimestamp(unix_time)
    t = swap_tz(time_utc, lat, lon)
    time_string = '%04d-%02d-%02d | %02d:%02d:%02d' % (t.year, t.month, t.day, t.hour, t.minute, t.second)

    return time_string


def where_are_you(location):
    """ input: string (location search)
       output: Nominatim object"""

    geolocator = Nominatim()
    return geolocator.geocode(location)


def get_iss_loc(location, source='ha'):
    """ input: location to search, string (optional)
       output: float, float, string, string"""

    location = where_are_you(location)

    try:
        lat = round(location.latitude, 4)
        lon = round(location.longitude, 4)
    except AttributeError:
        return '-', '-', 'Location not found!', ''

    if source == 'n2yo':
        # code for n2yo (magnitude seems to be underesimated)
        api = N2YO_API_KEY  # n2yo api, append to URL
        url = 'http://www.n2yo.com/rest/v1/satellite/visualpasses/25544/{}/{}/0/10/180/&apiKey={}'.format(lat, lon, api)
        response = requests.get(url)
        pass_info = ast.literal_eval(response.content.decode('utf-8'))

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
        pass_list = '\n'.join(pass_list)

    if source == 'ha':
        # heavens-above code(gives results in UTC; not easy to parse out either)
        url = 'https://www.heavens-above.com/PassSummary.aspx?satid=25544&lat={}&lng={}'.format(lat, lon)
        html = requests.get(url).content
        dataframe_list = pd.read_html(html)

        # this part contains the table if there is one
        try:
            dataframe = convert_columns(dataframe_list[4], lat, lon)
            if dataframe.empty:
                raise Exception
            else:
                # a few final formatting considerations
                pass_list = dataframe.to_string()\
                    .replace('Â', ' ')\
                    .replace(' °', '° ')\
                    .replace('Date', '    ', 1)\
                    .replace('Pass type', '         ', 1)
        except Exception:
            pass_list = 'No passes for the next ten days!'

    return lat, lon, pass_list, url


def whereis(*arg):
    """ input: string
       output: bool"""

    # Nomanatim geocoder
    location = where_are_you(arg)

    # return False if no location found
    try:
        lat = round(location.latitude, 6)
        lon = round(location.longitude, 6)
    except Exception:
        return False

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
    shortener = Shortener('Bitly', bitly_token=BITLY_TOKEN)

    return shortener.short(url)
