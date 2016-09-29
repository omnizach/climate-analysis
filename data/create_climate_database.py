from __future__ import print_function

import urllib2
import pyquery
import re
import gzip
import sqlite3
from math import *
from tqdm import tqdm

DIR_URL = 'ftp://ftp.ncdc.noaa.gov/pub/data/noaaglobaltemp/operational/gridded/'

PROXIES = {
    'http': 'http://proxy.jf.intel.com:911',
    'https': 'http://proxy.jf.intel.com:912',
    'ftp': 'http://proxy.jf.intel.com:911'
}

FILE_NAME = 'noaa_global_temp_grid.asc.gz'

DB = 'climate.db'

EARTH_RADIUS = 6350
AREA_FACTOR = EARTH_RADIUS * 2 * pi * EARTH_RADIUS * sin(5 * pi / 180.0) / 72.0


def get_file_url(listing_url):
    proxy = urllib2.ProxyHandler(PROXIES)
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)

    listing = urllib2.urlopen(listing_url).read()
    
    d = pyquery.PyQuery(listing)
    
    filename = [a.attr.href for a in d('a').items() if re.match(r'.*\.asc\.gz$', a.attr.href)][0]
    
    return listing_url + filename
    

def download_temp_grid_file(url):
    proxy = urllib2.ProxyHandler(PROXIES)
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)

    with open(FILE_NAME,'wb') as f:
        f.write(urllib2.urlopen(url).read())
        f.close()


def read_grid(filename):
    lats = [float(x) + 2.5 for x in range(-90, 90, 5)]
    longs = [float(x) + 2.5 for x in range(0, 360, 5)]

    with gzip.open(filename) as f:
        while True:
            line = f.readline()
            if not line:
                return
                
            month, year = [int(x) for x in line.strip().split(' ', 1)]

            for lat in lats:
                line = f.readline()
                if not line:
                    return
                ts = [float(x) for x in re.split('\s+', line.strip())]
                for lon, temp in zip(longs, ts):
                    yield {
                        'year': year,
                        'month': month,
                        'latitude': lat,
                        'longitude': lon,
                        'temperature': float(temp) if float(temp) > -999 else None
                    }


def create_db(db):
    with sqlite3.connect(db) as conn:
        conn.execute("""
            DROP TABLE IF EXISTS temps;
        """)

        conn.execute("""
            CREATE TABLE temps (
                year INT NOT NULL,
                month INT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                area REAL NOT NULL,
                temperature REAL NULL
            )
        """)

        conn.commit()


def five_degree_area(lat):
    '''Approximate area in square km of a 5 degree sector on a globe.'''
    return AREA_FACTOR * abs(cos(lat * pi / 180.0))


def insert_temps(filename, rows):
    with sqlite3.connect(filename) as conn:
        cur = conn.cursor()

        SQL = """INSERT INTO temps (year, month, latitude, longitude, area, temperature)
                 VALUES (:year, :month, :latitude, :longitude, :area, :temperature)
        """

        for row in tqdm(rows):
            row['area'] = five_degree_area(row['latitude'])
            
            cur.execute(SQL, row)
            
        conn.commit()



def row_count(filename):
    with sqlite3.connect(filename) as conn:
        cur = conn.cursor()
        cur.execute("select count(*) from temps")
        return cur.fetchone()[0]


if __name__ == '__main__':
    print('Downloading File')
    download_temp_grid_file(get_file_url(DIR_URL))
    print('Download Complete')

    print('Creating Database')
    create_db(DB)

    print('Inserting Rows')
    insert_temps(DB, read_grid(FILE_NAME))

    print('Inserted {0} rows'.format(row_count(DB)))
