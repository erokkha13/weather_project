from flask import Flask, render_template, request
import requests
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

app = Flask(__name__)
app.json.ensure_ascii = False

API_KEY = 'cv8VeHciL0CyfUmikfoT6YdG0AgrAvUH'

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
        params_weather = {'apikey': API_KEY, 'details': 'true', 'metric': 'true'}
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
    except requests.exceptions.HTTPError as err:
        if r_weather.status_code == 404:
            raise ValueError('Неправильные данные')
        elif r_weather.status_code == 503:
            raise PermissionError('API не работают')
        else:
            raise PermissionError('Доступ запрещен')
    except Exception as error:
        raise

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

            # Сохраним данные о погоде в сессии
            app.config['start_weather'] = start_weather
            app.config['end_weather'] = end_weather

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


# Dash integration
app_dash = Dash(__name__, server=app, routes_pathname_prefix='/dash/')

app_dash.layout = html.Div([
    html.A("Вернуться к результатам", href='/', className='button-return'),  # Кнопка для возврата
    dcc.Dropdown(
        id='weather-parameter',
        options=[
            {'label': 'Температура', 'value': 'temperature'},
            {'label': 'Скорость ветра', 'value': 'wind'},
            {'label': 'Вероятность осадков', 'value': 'precipitation'},
        ],
        value='temperature'
    ),
    dcc.Graph(id='weather-graph'),
])

@app_dash.callback(
    Output('weather-graph', 'figure'),
    [Input('weather-parameter', 'value')]
)
def update_graph(parameter):
    start_weather = app.config.get('start_weather')
    end_weather = app.config.get('end_weather')
    start_city = 'Начальный город'
    end_city = 'Конечный город'
    if not start_weather or not end_weather:
        return go.Figure()

    start_temp = start_weather['temperature_celsius']
    end_temp = end_weather['temperature_celsius']
    start_wind = start_weather['wind_speed_kmh']
    end_wind = end_weather['wind_speed_kmh']
    start_precip = start_weather['precipitation_probability_percent']
    end_precip = end_weather['precipitation_probability_percent']

    if parameter == 'temperature':
        figure = go.Figure()
        figure.add_trace(go.Bar(
            x=[start_city, end_city],
            y=[start_temp, end_temp],
            name='Температура (°C)',
            marker_color='blue'
        ))
    elif parameter == 'wind':
        figure = go.Figure()
        figure.add_trace(go.Scatter(
            x=[start_city, end_city],
            y=[start_wind, end_wind],
            mode='lines+markers',
            name='Скорость ветра (км/ч)',
            marker=dict(color='orange'),
        ))
    else:
        figure = go.Figure()
        figure.add_trace(go.Bar(
            x=[start_city, end_city],
            y=[start_precip, end_precip],
            name='Вероятность осадков (%)'
        ))

    figure.update_layout(title='Погодные данные',
                         xaxis_title='Города',
                         yaxis_title='Значение')
    return figure

if __name__ == '__main__':
    app.run(debug=True)


