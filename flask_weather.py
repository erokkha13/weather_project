from flask import Flask, render_template, request
import requests

app = Flask(__name__)
app.json.ensure_ascii = False

API_KEY = 'pGgYoPHTyfpCPY9vDwUYmVYyCy1fAGfd'

def fetch_location(city):
    try:
        url = "http://dataservice.accuweather.com/locations/v1/cities/search"
        params = {
            'apikey': API_KEY,
            'q': city,
            'language': 'ru-RU',
            'details': 'false',
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        if not data:
            raise ValueError(f"Город '{city}' не найден. Проверьте правильность ввода.")

        location = data[0]
        return {
            'key': location['Key'],
            'latitude': location['GeoPosition']['Latitude'],
            'longitude': location['GeoPosition']['Longitude']
        }

    except requests.exceptions.Timeout:
        raise ConnectionError("Превышено время ожидания ответа от сервера.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к серверу.")
    except requests.exceptions.HTTPError as err:
        if response.status_code == 401:
            raise PermissionError("Неверный API-ключ.")
        elif response.status_code == 403:
            raise PermissionError("Доступ к API запрещён.")
        elif response.status_code == 404:
            raise ValueError(f"Город '{city}' не найден.")
        else:
            raise Exception(f"Ошибка HTTP при поиске города: {err}")
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise Exception(f"Произошла ошибка при поиске города: {e}")


def fetch_weather(location_key):
    try:
        try:
            params_weather = {'apikey': API_KEY,
                              'details': 'true',
                              'metric': 'true'}
            r_weather = requests.get('http://dataservice.accuweather.com/forecasts/v1/hourly/1hour/' + location_key, params=params_weather)
            r_weather.raise_for_status()
            weather_json = r_weather.json()
            temp = weather_json[0]['Temperature']['Value']
            humidity = weather_json[0]['RelativeHumidity']
            speed_wind = weather_json[0]['Wind']['Speed']['Value']
            probability = weather_json[0]['PrecipitationProbability']
            return {
                'temperature_celsius': temp,
                'humidity_percent': humidity,
                'wind_speed_kmh': speed_wind,
                'precipitation_probability_percent': probability
            }
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Не удалось подключиться к серверу")
        except requests.exceptions.HTTPError:
            if r_weather.status_code == 404:
                raise ValueError('Неправильные данные')
            elif r_weather.status_code == 503:
                raise PermissionError('API не работают')
            else:
                raise PermissionError('Доступ запрещен')
        except Exception as error:
            print(f'Произошла неизвестная ошибка: {error}')

    except requests.exceptions.Timeout:
        raise ConnectionError("Превышено время ожидания ответа от сервера погоды.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Не удалось подключиться к серверу погоды.")
    except requests.exceptions.HTTPError as err:
        if response.status_code == 401:
            raise PermissionError("Неверный API-ключ для получения погоды.")
        elif response.status_code == 403:
            raise PermissionError("Доступ к API погоды запрещён.")
        elif response.status_code == 404:
            raise ValueError("Данные о погоде не найдены для заданных координат.")
        else:
            raise Exception(f"Ошибка HTTP при получении погоды: {err}")
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise Exception(f"Ошибка при получении погоды: {e}")

def evaluate_weather(temp, wind, precip):
    if temp < 0:
        if precip < 20:
            if wind < 20:
                return 'Наденьте куртку! Погода безснежная, ветра нет'
            elif wind < 30:
                return 'Наденьте куртку! Ветер умеренный, снега нет'
            else:
                return 'Наденьте куртку! Снега нет, ветер сильный'
        elif 20 <= precip <= 50:
            if wind < 20:
                return 'Наденьте куртку! Скорее всего будет снег, ветра нет'
            elif wind < 30:
                return 'Наденьте куртку! Ветер умеренный, скорее всего будет снег'
            else:
                return 'Наденьте куртку! Ветер сильный, скорее всего будет снег'
        else:
            if wind < 20:
                return 'Наденьте куртку! На улице снег, ветра нет'
            elif wind < 30:
                return 'Наденьте куртку! Ветер умеренный, на улице снег'
            else:
                return 'Наденьте куртку! Ветер сильный, на улице снег'

    elif 0 <= temp <= 15:
        if precip < 20:
            if wind < 20:
                return 'Температура приятная! Дождя и ветра нет'
            elif wind < 30:
                return 'Температура приятная! Дождя нет, ветер умеренный'
            else:
                return 'Температура приятная! Дождя нет, ветер сильный'
        elif 20 <= precip <= 50:
            if wind < 20:
                return 'Температура приятная! Скорее всего будет дождь, ветра нет'
            elif wind < 30:
                return 'Температура приятная! Скорее всего будет дождь, ветер умеренный'
            else:
                return 'Температура приятная! Скорее всего будет дождь, сильный ветер'
        else:
            if wind < 20:
                return 'Температура приятная! Будет дождь, ветра нет'
            elif wind < 30:
                return 'Температура приятная! Будет дождь, ветер умеренный'
            else:
                return 'Температура приятная! Будет дождь, ветер сильный'

    else:
        if precip < 20:
            if wind < 20:
                return 'Жара! Дождя и ветра нет'
            elif wind < 30:
                return 'Жара! Дождя нет, ветер умеренный'
            else:
                return 'Жара! Дождя нет, ветер сильный'
        elif 20 <= precip <= 50:
            if wind < 20:
                return 'Жара! Скорее всего будет дождь, ветра нет'
            elif wind < 30:
                return 'Жара! Скорее всего будет дождь, ветер умеренный'
            else:
                return 'Жара! Скорее всего будет дождь, сильный ветер'
        else:
            if wind < 20:
                return 'Жара! Будет дождь, ветра нет'
            elif wind < 30:
                return 'Жара! Будет дождь, ветер умеренный'
            else:
                return 'Жара! Будет дождь, ветер сильный'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')

        if not start_city or not end_city:
            return render_template('index.html', error="Пожалуйста, укажите начальную и конечную точки маршрута.")

        try:
            start_loc = fetch_location(start_city)
            start_weather = fetch_weather(start_loc['key'])
            start_evaluation = evaluate_weather(
                start_weather['temperature_celsius'],
                start_weather['wind_speed_kmh'],
                start_weather['precipitation_probability_percent']
            )

            end_loc = fetch_location(end_city)
            end_weather = fetch_weather(end_loc['key'])
            end_evaluation = evaluate_weather(
                end_weather['temperature_celsius'],
                end_weather['wind_speed_kmh'],
                end_weather['precipitation_probability_percent']
            )

            result = {
                'start_city': start_city,
                'start_weather': start_weather,
                'start_condition': start_evaluation,
                'end_city': end_city,
                'end_weather': end_weather,
                'end_condition': end_evaluation
            }

            return render_template('result.html', result=result)

        except (ValueError, PermissionError, ConnectionError, KeyError) as error:
            return render_template('index.html', error=str(error))
        except Exception as e:
            return render_template('index.html', error=f"Неизвестная ошибка: {e}")

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)