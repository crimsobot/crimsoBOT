from collections import namedtuple
from typing import List, Optional, Tuple

import aiohttp
import pendulum
import tabulate
from geopy.geocoders import Nominatim
from geopy.location import Location
from lxml import html
from pyshorteners import Shortener
from timezonefinder import TimezoneFinder

from config import BITLY_TOKEN, MAPQUEST_API_KEY


ISSPass = namedtuple(
    'ISSPass',
    'date mag start_time start_alt start_az highest_time highest_alt highest_az end_time end_alt end_az'
)


# Convert heavens-above data from UTC to local time
def swap_tz(time_string: str, lat: float, lon: float) -> pendulum.DateTime:
    timezone = TimezoneFinder().timezone_at(lng=lon, lat=lat)
    # Ignored because .parse() is Union[Date, Time, DateTime, Duration] - and only DateTime has .in_timezone()
    time = pendulum.parse(time_string).in_timezone(timezone)  # type: ignore

    return time


def where_are_you(location: str) -> Optional[Location]:
    """ input: string (location search)
       output: Nominatim object"""

    geolocator = Nominatim(user_agent='crimsoBOT/astronomy')
    return geolocator.geocode(location)


async def get_iss_loc(query: str) -> Tuple[Optional[float], Optional[float], Optional[str], List[ISSPass]]:
    location = where_are_you(query)
    if not location:
        return None, None, None, []

    lat = round(location.latitude, 4)
    lon = round(location.longitude, 4)

    url = 'https://www.heavens-above.com/PassSummary.aspx?satid=25544&lat={}&lng={}'.format(lat, lon)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            text = await response.text()
            tree = html.fromstring(text.strip('Â'))

    prefix = '/html/body/form/table/tr[3]/td[1]/table[3]/tr'
    rows = []

    for table_row in range(1, 11):
        row_exists = tree.xpath(f'{prefix}[{table_row}]')
        if not row_exists:
            break

        # The first item in this list is the 'date' cell of the current table row. Since this specific column is
        # structured differently in the html, we can't get its value the same way we do for all of the other cells.
        data = [tree.xpath(f'{prefix}[{table_row}]/td[1]/a')[0].text]
        for item in range(2, 12):  # We start at 2 since we already have cell 1 of this row
            result = tree.xpath(f'{prefix}[{table_row}]/td[{item}]')[0].text
            if item in (3, 6, 9):  # These are time strings - we need to swap them to local time
                result = swap_tz(result, lat, lon).format('h:mm A')

            data.append(result)

        # Pack all of the data into a namedtuple
        rows.append(ISSPass(*data))

    return lat, lon, url, rows


def format_passes(passes: List[ISSPass]) -> str:
    headers = [
        '\nDate',
        '\nMag.',
        'Start\nTime',
        '\nAlt.',
        '\nAz.',
        'Highest \nTime',
        '\nAlt.',
        '\nAz.',
        'End\nTime',
        '\nAlt.',
        '\nAz.',
    ]

    return tabulate.tabulate(passes, headers=headers)


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
