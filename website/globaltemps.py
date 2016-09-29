import os
import sqlite3
from math import pi, sin

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/climate.db')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def yearly_averages(lats, longs, months):

    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT year, SUM(temperature * area) / SUM(area) AS temp 
            FROM temps
            WHERE latitude >= :lat_start AND latitude <= :lat_end AND
                longitude >= :long_start AND longitude <= :long_end AND
                month >= :month_start AND month <= :month_end
            GROUP BY year
            ORDER BY year""", {
            'lat_start': lats[0],
            'lat_end': lats[1],
            'long_start': longs[0],
            'long_end': longs[1],
            'month_start': months[0],
            'month_end': months[1]
        })

        return [dict_factory(cur, r) for r in cur.fetchall()]


def latitude_averages(longs, months, years):
    
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT latitude, AVG(temperature) AS temp FROM temps
            WHERE year >= :year_start AND year <= :year_end AND
                longitude >= :long_start AND longitude <= :long_end AND
                month >= :month_start AND month <= :month_end
            GROUP BY latitude
            ORDER BY latitude""", {
            'year_start': years[0],
            'year_end': years[1],
            'long_start': longs[0],
            'long_end': longs[1],
            'month_start': months[0],
            'month_end': months[1]
        })

        return [dict_factory(cur, r) for r in cur.fetchall()]