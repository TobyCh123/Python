import requests
import csv
from datetime import datetime
from statistics import mean, mode

'''
MET API Documentation links:
References found at this link: https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/data/datapoint_api_reference.pdf
Used to get list of regions/codes: http://datapoint.metoffice.gov.uk/public/data/txt/wxfcs/regionalforecast/json/sitelist?key='+APIkey
'''


# Get the intitial data from MET
def get_weather(region_number, api_key):
    url = f'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/{region_number}?res=daily&key={api_key}'
    try:
        response = requests.get(url)
        weather_data = response.json()
        return weather_data
    except Exception as e:
        print(f'Error for region {region_number}: {e}, couldn\'t get weather')
        return None


# Formats date to ensure consistent
def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%dZ')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return 'N/A'


# Looks up code from json in dictionary from MET to get descriptions
def translate_region(region_code):
    region_codes = {
        501: 'HE',  # Scotland
        516: 'WL',  # Wales
        507: 'NW',  # North
        508: 'NE',  # North
        509: 'YH',  # North
        510: 'WM',  # Midlands/West
        511: 'EM',  # Midlands/East
        512: 'EE',  # East
        513: 'SW',  # South
        514: 'SE'   # South/London
        }
    return region_codes.get(int(region_code), 'Unknown')


# Looks up code from json in dictionary from MET to get description
def translate_weather_type(weather_code):
    weather_types = {
        'NA': 'Not available',
        0: 'Clear night',
        1: 'Sunny day',
        2: 'Partly cloudy (night)',
        3: 'Partly cloudy (day)',
        4: 'Not used',
        5: 'Mist',
        6: 'Fog',
        7: 'Cloudy',
        8: 'Overcast',
        9: 'Light rain shower (night)',
        10: 'Light rain shower (day)',
        11: 'Drizzle',
        12: 'Light rain',
        13: 'Heavy rain shower (night)',
        14: 'Heavy rain shower (day)',
        15: 'Heavy rain',
        16: 'Sleet shower (night)',
        17: 'Sleet shower (day)',
        18: 'Sleet',
        19: 'Hail shower (night)',
        20: 'Hail shower (day)',
        21: 'Hail',
        22: 'Light snow shower (night)',
        23: 'Light snow shower (day)',
        24: 'Light snow',
        25: 'Heavy snow shower (night)',
        26: 'Heavy snow shower (day)',
        27: 'Heavy snow',
        28: 'Thunder shower (night)',
        29: 'Thunder shower (day)',
        30: 'Thunder'
    }
    return weather_types.get(int(weather_code), 'Unknown')


# Looks up code from json in dictionary from MET to get description
def translate_visibility(visibility_code):
    visibility_dict = {
        'UN': 'Unknown',
        'VP': 'Very Poor',
        'PO': 'Poor',
        'MO': 'Moderate',
        'GO': 'Good',
        'VG': 'Very Good',
        'EX': 'Excellent'
    }
    return visibility_dict.get(visibility_code, 'Unknown')


# Loops through data to get for each region
def get_weather_for_regions(region_list, api_key):
    weather_list = []
    today_date = datetime.now().strftime('%Y-%m-%d')
    for region_number in region_list:
        weather_data = get_weather(region_number, api_key)
        if weather_data:
            for period in weather_data.get('SiteRep', {}
                                           ).get('DV', {}
                                                 ).get('Location', {}
                                                       ).get('Period', []):
                period_date = format_date(period['value'])
                # Only want todays forecast - future ones may be less accurate
                if period_date == today_date:
                    weather = {
                        'Date': period_date,
                        'Region': translate_region(region_number),
                        'WeatherType': translate_weather_type(period['Rep'][0]['W']),
                        'MaxFeelTemp': period['Rep'][0]['FDm'],
                        'MaxTemp': period['Rep'][0]['Dm'],
                        'ProbPrec': period['Rep'][0]['PPd'],
                        'WindSpeed': period['Rep'][0]['S'],
                        'Visibility': translate_visibility(period['Rep'][0]['V'])
                    }
                    weather_list.append(weather)
    return weather_list


# Calculates mean for number based results for 'general GB' (999)
def calculate_mean(data, key):
    values = [int(entry[key]) for entry in data]
    return mean(values)


# Calculates mode for word based results for 'general GB' (999)
def calculate_mode(data, key):
    values = [entry[key] for entry in data]
    return mode(values)


# Calculates the average of the weather outputs for a 'general GB' (999)
def get_region_999(weather_data):
    avg_maxfeeltemp = calculate_mean(weather_data, 'MaxFeelTemp')
    avg_maxtemp = calculate_mean(weather_data, 'MaxTemp')
    avg_probprec = calculate_mean(weather_data, 'ProbPrec')
    avg_windspeed = calculate_mean(weather_data, 'WindSpeed')
    mode_weathertype = calculate_mode(weather_data, 'WeatherType')
    mode_visibility = calculate_mode(weather_data, 'Visibility')

    region_999 = {
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Region': 'Average',
        'WeatherType': mode_weathertype,
        'MaxFeelTemp': avg_maxfeeltemp,
        'MaxTemp': avg_maxtemp,
        'ProbPrec': avg_probprec,
        'WindSpeed': avg_windspeed,
        'Visibility': mode_visibility
    }
    return region_999


# Save the final data to a csv - appends new records to existing file
def save_to_csv(data, filename):
    column_headers = ['Date',
                      'Region',
                      'WeatherType',
                      'MaxFeelTemp',
                      'MaxTemp',
                      'ProbPrec',
                      'WindSpeed',
                      'Visibility']
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_headers)
        writer.writerows(data)


# Execute code
if __name__ == '__main__':
    api_key = ''
    region_list = [501, 516, 507, 508, 509, 510, 511, 512, 513, 514]
    weather_data = get_weather_for_regions(region_list, api_key)
    if weather_data:
        # Append the calculated values for region 999 and save
        weather_data.append(get_region_999(weather_data))
        save_to_csv(weather_data, 'weather_data.csv')
        print('Weather data saved successfully!')
    else:
        print('Failed to fetch weather data.')
