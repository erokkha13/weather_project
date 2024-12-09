from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

API_KEY = 'jyKafXwbRGuHU20upPyOc6P8PePwutoe'


def get_weather_data(latitude, longitude):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
    params = {
        'apikey': API_KEY,
        'q': f"{latitude},{longitude}"
    }
    location_response = requests.get(location_url, params=params)
    if location_response.status_code != 200:
        raise Exception("Ошибка при получении Location Key")

    location_data = location_response.json()
    location_key = location_data.get('Key')
    if not location_key:
        raise Exception("Location Key не найден")

    weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    params = {
        'apikey': API_KEY,
        'details': 'true'
    }
    weather_response = requests.get(weather_url, params=params)
    if weather_response.status_code != 200:
        raise Exception("Ошибка при получении погодных данных")

    weather_data = weather_response.json()
    if not weather_data:
        raise Exception("Нет данных о погоде")

    return weather_data[0]


def extract_key_parameters(weather_json):
    try:
        temperature = weather_json['Temperature']['Metric']['Value']
        humidity = weather_json['RelativeHumidity']
        wind_speed = weather_json['Wind']['Speed']['Metric']['Value']
        precipitation_probability = weather_json.get('PrecipitationProbability', 0)

        return {
            'temperature_celsius': temperature,
            'humidity_percent': humidity,
            'wind_speed_kmh': wind_speed,
            'precipitation_probability_percent': precipitation_probability
        }
    except KeyError as e:
        raise Exception(f"Отсутствует ожидаемый ключ в данных: {e}")


@app.route('/weather', methods=['GET'])
def weather():
    try:
        latitude = request.args.get('latitude', type=float)
        longitude = request.args.get('longitude', type=float)

        if latitude is None or longitude is None:
            return jsonify({'error': 'Необходимо указать latitude и longitude'}), 400

        weather_json = get_weather_data(latitude, longitude)
        key_parameters = extract_key_parameters(weather_json)

        return jsonify(key_parameters)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)