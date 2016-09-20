from __future__ import print_function

import cherrypy
import json
import os
import sys
from math import cos, sin, pi

class GlobalTemps:
    def __init__(self):

        # Load data into big list
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/global-temps.tsv')) as f:
            f.readline() # header: year month latitude longitude temperature
            self.temps = []
            for line in f:
                yr, mon, lat, lon, temp = line.strip().split('\t')
                self.temps.append({
                    'year': int(yr),
                    'month': int(mon),
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'temperature': float(temp) if float(temp) > -999 else None
                })

    @cherrypy.expose
    def current(self):
        '''Returns all temperatures for the latest month in the data set.'''

        # response is json so the browser parses the data
        cherrypy.response.headers['Content-Type'] = 'application/json'

        # get the latest month/year by just grabbing it from the last row
        month, year = self.temps[-1]['month'], self.temps[-1]['year']

        # filter just for the current month/year
        # because we know the data is fixed length, we could also just slice the end of the array
        # and take the last 36*72 rows. This solution is a bit more generic.
        return json.dumps([t for t in self.temps if t['month'] == month and t['year'] == year])

    @cherrypy.expose
    def yearly_averages(self, lat_start=-87.5, lat_end=87.5, long_start=0.0, long_end=360, month_start=1, month_end=12, *args, **kwargs):
        '''Yearly temperature averages globally.'''
        lat_start = float(lat_start)
        lat_end = float(lat_end)
        long_start = float(long_start)
        long_end = float(long_end)
        month_start = int(month_start)
        month_end = int(month_end)

        print(lat_start, lat_end, long_start, long_end, month_start, month_end)

        # response is json so the browser parses the data
        cherrypy.response.headers['Content-Type'] = 'application/json'

        EARTH_RADIUS = 6350
        AREA_FACTOR = EARTH_RADIUS * 2 * pi * EARTH_RADIUS * sin(5 * pi / 180.0) / 72.0

        avgs = [{'sum':0, 'count':0} for x in range(1880, 2017)]

        for t in self.temps:
            if t['temperature'] is None or \
               t['latitude'] < lat_start   or t['latitude'] > lat_end or \
               t['longitude'] < long_start or t['longitude'] > long_end or \
               t['month'] < month_start    or t['month'] > month_end:
                continue

            area = AREA_FACTOR * abs(cos(t['latitude'] * pi / 180.0))
            avgs[t['year'] - 1880]['count'] += area
            avgs[t['year'] - 1880]['sum'] += area * t['temperature']

        return json.dumps([{ 'year': i+1880, 'average': x['sum'] / x['count'] if x['count'] > 0 else None } for i, x in enumerate(avgs)])

    @cherrypy.expose
    def latitude_averages(self, year_start=1880, year_end=3000, long_start=0.0, long_end=360, month_start=1, month_end=12, *args, **kwargs):
        '''Distribution  of averages across latitudes'''

        year_start = int(year_start)
        year_end = int(year_end)
        long_start = float(long_start)
        long_end = float(long_end)
        month_start = int(month_start)
        month_end = int(month_end)

        cherrypy.response.headers['Content-Type'] = 'application/json'

        avgs = [{'sum':0, 'count':0} for x in range(36)]

        for t in self.temps:
            if t['temperature'] is None or \
               t['year'] < year_start or t['year'] > year_end or \
               t['longitude'] < long_start or t['longitude'] > long_end or \
               t['month'] < month_start or t['month'] > month_end:
                continue

            bin = int(t['latitude']+87.5)/5
            avgs[bin]['count'] += 1
            avgs[bin]['sum'] += t['temperature']

        return json.dumps([{ 'latitude': i * 5 - 87.5, 'average': x['sum'] / x['count'] if x['count'] > 0 else None } for i, x in enumerate(avgs)])

class Root:

    globaltemps = GlobalTemps()

    def __init__(self):
        self._cp_config = {'tools.staticdir.on' : True,
                            'tools.staticdir.dir' : os.path.join(os.path.dirname(os.path.abspath(__file__)), '../client'),
                            'tools.staticdir.index' : 'index.html',
                            'tools.staticdir.content_types': {'css': 'text/css',
                                                             'js': 'application/javascript',
                                                             'png': 'image/png',
                                                             'html': 'text/html',
                                                             'json': 'application/json' } }


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8081'))

    cherrypy.config.update({ 'server.socket_host': '0.0.0.0',
                             'server.socket_port': port })

    cherrypy.quickstart(Root())