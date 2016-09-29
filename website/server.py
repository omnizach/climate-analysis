from flask import Flask, url_for, request, jsonify
import globaltemps as gt

app = Flask(__name__, static_url_path='')

def float_range(s):
    try:
        return tuple([float(x) for x in s.split(',', 1)])
    except Error:
        raise ValueError

@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/avg_temps_by_year')
def yearly_averages():
    lats = request.args.get('lats', (-87.5,87.5), float_range)
    longs = request.args.get('longs', (0,360), float_range)
    months = request.args.get('months', (1,12), float_range)

    return jsonify(gt.yearly_averages(lats, longs, months))


@app.route('/avg_temps_by_latitude')
def latitude_averages():
    longs = request.args.get('longs', (0,360), float_range)
    months = request.args.get('months', (1,12), float_range)
    years = request.args.get('years', (1880,2017), float_range)
    
    return jsonify(gt.latitude_averages(longs, months, years))


@app.route('/test')
def test():
    lats = request.args.get('lats', (-87.5,87.5), float_range)
    return jsonify(lats)