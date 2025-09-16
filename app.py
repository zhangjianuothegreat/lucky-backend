from flask import Flask, request, render_template, url_for, jsonify

import sqlite3

from lunar_python import Solar, Lunar

from dateutil.parser import parse



app = Flask(__name__)

app.secret_key = 'your-secret-key'  # Replace with a secure key

app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force reload templates



# SQLite database path

DB_PATH = r"D:\xampp\htdocs\zen\luckytown\cities.db"



# 28 Lunar Mansions and Five Elements

CONSTELLATIONS = [

    ("Jiao Xiu", "Azure Dragon", "Wood"), ("Kang Xiu", "Azure Dragon", "Metal"), ("Di Xiu", "Azure Dragon", "Earth"),

    ("Fang Xiu", "Azure Dragon", "Wood"), ("Xin Xiu", "Azure Dragon", "Fire"), ("Wei Xiu", "Azure Dragon", "Fire"),

    ("Ji Xiu", "Azure Dragon", "Water"), ("Dou Xiu", "Black Tortoise", "Wood"), ("Niu Xiu", "Black Tortoise", "Metal"),

    ("Nü Xiu", "Black Tortoise", "Earth"), ("Xu Xiu", "Black Tortoise", "Water"), ("Wei Xiu", "Black Tortoise", "Water"),

    ("Shi Xiu", "Black Tortoise", "Fire"), ("Bi Xiu", "Black Tortoise", "Water"), ("Kui Xiu", "White Tiger", "Wood"),

    ("Lou Xiu", "White Tiger", "Metal"), ("Wei Xiu", "White Tiger", "Earth"), ("Mao Xiu", "White Tiger", "Fire"),

    ("Bi Xiu", "White Tiger", "Water"), ("Zui Xiu", "White Tiger", "Fire"), ("Shen Xiu", "White Tiger", "Water"),

    ("Jing Xiu", "Vermilion Bird", "Wood"), ("Gui Xiu", "Vermilion Bird", "Metal"), ("Liu Xiu", "Vermilion Bird", "Earth"),

    ("Xing Xiu", "Vermilion Bird", "Fire"), ("Zhang Xiu", "Vermilion Bird", "Fire"), ("Yi Xiu", "Vermilion Bird", "Fire"),

    ("Zhen Xiu", "Vermilion Bird", "Water")

]



# Five Elements with weights

FIVE_ELEMENTS = {

    'Wood': {'generates': ['Fire'], 'destroys': ['Metal'], 'same': ['Wood'], 'weight': 0.8},

    'Fire': {'generates': ['Earth'], 'destroys': ['Water'], 'same': ['Fire'], 'weight': 0.7},

    'Earth': {'generates': ['Metal'], 'destroys': ['Wood'], 'same': ['Earth'], 'weight': 0.6},

    'Metal': {'generates': ['Water'], 'destroys': ['Fire'], 'same': ['Metal'], 'weight': 0.7},

    'Water': {'generates': ['Wood'], 'destroys': ['Earth'], 'same': ['Water'], 'weight': 0.6}

}



# Template filter for constellation translation

@app.template_filter('translate_constellation')

def translate_constellation(constellation):

    translations = {

        'Jiao Xiu': 'The Horn', 'Kang Xiu': 'The Neck', 'Di Xiu': 'The Root',

        'Fang Xiu': 'The Room', 'Xin Xiu': 'The Heart', 'Wei Xiu': 'The Tail',

        'Ji Xiu': 'The Winnowing Basket', 'Dou Xiu': 'The Dipper', 'Niu Xiu': 'The Ox',

        'Nü Xiu': 'The Girl', 'Xu Xiu': 'The Void', 'Wei Xiu': 'The Rooftop',

        'Shi Xiu': 'The Encampment', 'Bi Xiu': 'The Wall', 'Kui Xiu': 'The Legs',

        'Lou Xiu': 'The Bond', 'Wei Xiu': 'The Stomach', 'Mao Xiu': 'The Pleiades',

        'Bi Xiu': 'The Net', 'Zui Xiu': 'The Beak', 'Shen Xiu': 'The Three Stars',

        'Jing Xiu': 'The Well', 'Gui Xiu': 'The Ghost', 'Liu Xiu': 'The Willow',

        'Xing Xiu': 'The Star', 'Zhang Xiu': 'The Extended Net', 'Yi Xiu': 'The Wings',

        'Zhen Xiu': 'The Chariot'

    }

    return translations.get(constellation, constellation)



# Calculate Bazi (Heavenly Stem for user element)

def calculate_bazi(date_str):

    try:

        year, month, day = map(int, date_str.split('-'))

        solar = Solar.fromYmd(year, month, day)

        lunar = solar.getLunar()

        bazi = lunar.getEightChar()

        day_stem = bazi.getDayGan()

        gan_to_element = {

            "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire", "戊": "Earth",

            "己": "Earth", "庚": "Metal", "辛": "Metal", "壬": "Water", "癸": "Water"

        }

        return day_stem, gan_to_element.get(day_stem, "Water")

    except Exception as e:

        print(f"Bazi calculation error ({date_str}): {e}")

        return None, None



# Get constellation (for cities) and element (for user)

def get_constellation_and_element(date_str, for_user=False):

    if not date_str:

        return None, None

    try:

        solar = Solar.fromYmd(*map(int, date_str.split('-')))

        lunar = solar.getLunar()

        lunar_day = lunar.getDay()

        constellation_idx = (lunar_day - 1) % 28

        constellation = CONSTELLATIONS[constellation_idx][0]

        if for_user:

            # For user, element comes from Bazi day stem

            day_stem, element = calculate_bazi(date_str)

        else:

            # For cities, element comes from constellation

            element = CONSTELLATIONS[constellation_idx][2]

        return constellation, element

    except (ValueError, IndexError, TypeError) as e:

        print(f"Date parsing error ({date_str}): {e}")

        return None, None

    except Exception as e:

        print(f"Unknown error processing date ({date_str}): {e}")

        return None, None



# Calculate match score

def calculate_match_score(user_element, user_const, city_element, city_const):

    if user_element is None or city_element is None:

        return 50

    if city_element in FIVE_ELEMENTS[user_element]['generates']:

        base_score = 90

    elif city_element in FIVE_ELEMENTS[user_element]['same']:

        base_score = 75

    elif city_element in FIVE_ELEMENTS[user_element]['destroys']:

        base_score = 30

    else:

        base_score = 50

    constellation_bonus = 15 if city_const in ["Jiao Xiu", "Dou Xiu", "Kui Xiu", "Jing Xiu"] else 0

    user_weight = FIVE_ELEMENTS.get(user_element, {}).get('weight', 0.7)

    city_weight = FIVE_ELEMENTS.get(city_element, {}).get('weight', 0.7)

    strength_bonus = round((user_weight + city_weight - 1.2) * 25)

    final_score = base_score + constellation_bonus + strength_bonus

    return max(0, min(round(final_score), 99))



# Get countries and states

def get_countries_and_states():

    try:

        with sqlite3.connect(DB_PATH) as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT country FROM cities WHERE country IS NOT NULL ORDER BY country")

            countries = [row[0] for row in cursor.fetchall()]

            country_to_states = {}

            for country in countries:

                cursor.execute("""

                    SELECT DISTINCT state_country 

                    FROM cities 

                    WHERE country = ? 

                    AND state_country IS NOT NULL 

                    AND state_country != 'Unknown' 

                    ORDER BY state_country

                """, (country,))

                states = [row[0] for row in cursor.fetchall()]

                country_to_states[country] = states

        return countries, country_to_states

    except sqlite3.Error as e:

        print(f"Database error: {e}")

        return [], {}



# Validate date

def validate_date(date_str):

    try:

        parsed_date = parse(date_str)

        return parsed_date.strftime('%Y-%m-%d') == date_str

    except ValueError:

        return False



# Get paginated cities

def get_paginated_cities(selected_country, selected_state, page, user_element, user_const, sort_order='desc'):

    try:

        page_size = 10

        offset = (page - 1) * page_size

        with sqlite3.connect(DB_PATH) as conn:

            cursor = conn.cursor()

            query = """

                SELECT name, country, state_country, incorporation_date, description 

                FROM cities 

                WHERE incorporation_date IS NOT NULL

            """

            params = []

            if selected_country != 'All':

                query += " AND country = ?"

                params.append(selected_country)

            if selected_state != 'All':

                query += " AND state_country = ?"

                params.append(selected_state)

            count_query = f"SELECT COUNT(*) FROM ({query})"

            cursor.execute(count_query, params)

            total_matches = cursor.fetchone()[0]

            query += " ORDER BY name LIMIT ? OFFSET ?"

            params.extend([page_size, offset])

            cursor.execute(query, params)

            cities = cursor.fetchall()

            cities_list = []

            for city in cities:

                name, country, state_country, incorporation_date, description = city

                city_const, city_element = get_constellation_and_element(incorporation_date, for_user=False)

                match_score = calculate_match_score(user_element, user_const, city_element, city_const)

                cities_list.append({

                    'name': name,

                    'country': country,

                    'state_country': state_country,

                    'incorporation_date': incorporation_date,

                    'description': description,

                    'match_score': match_score,

                    'constellation': city_const,

                    'element': city_element

                })

            cities_list.sort(key=lambda x: x['match_score'], reverse=(sort_order == 'desc'))

        return cities_list, total_matches

    except sqlite3.Error as e:

        print(f"Database query error: {e}")

        return [], 0



# Main route

@app.route('/', methods=['GET', 'POST'])

@app.route('/match_cities', methods=['GET', 'POST'])

def index():

    birth_date = ''

    selected_country = 'All'

    selected_state = 'All'

    manual_city = ''

    manual_date = ''

    cities = []

    manual_result = None

    total_matches = 0

    user_const = None

    user_element = None

    error = None

    sort_order = request.args.get('sort', 'desc')

    page = int(request.args.get('page', 1))

    countries, country_to_states = get_countries_and_states()

    small_countries = ['Hong Kong', 'Singapore']

    states = ['All']



    if request.method == 'POST':

        birth_date = request.form.get('birth_date', '').strip()

        selected_country = request.form.get('country', 'All')

        selected_state = request.form.get('state_country', 'All')

        manual_city = request.form.get('manual_city', '').strip()

        manual_date = request.form.get('manual_date', '').strip()

        page = int(request.args.get('page', 1))

        sort_order = request.args.get('sort', sort_order)

        if selected_country != 'All' and selected_country not in small_countries:

            states = ['All'] + country_to_states.get(selected_country, [])

        elif selected_country in small_countries:

            states = ['All']

        if not birth_date:

            error = 'Please enter your birth date (e.g., 19900515).'

        elif not validate_date(birth_date):

            error = 'Invalid date format. Please use YYYYMMDD (e.g., 19900515).'

        else:

            user_const, user_element = get_constellation_and_element(birth_date, for_user=True)

            if not user_const:

                error = 'Invalid birth date. Please use YYYYMMDD (e.g., 19900515).'

        if manual_city and manual_date and not error:

            if not validate_date(manual_date):

                error = 'Invalid city founding date. Please use YYYYMMDD (e.g., 18680903).'

            else:

                manual_const, manual_element = get_constellation_and_element(manual_date, for_user=False)

                if manual_const:

                    manual_score = calculate_match_score(user_element, user_const, manual_element, manual_const)

                    manual_result = {

                        'city': manual_city,

                        'date': manual_date,

                        'score': manual_score,

                        'constellation': manual_const,

                        'element': manual_element

                    }

                else:

                    error = 'Invalid city founding date. Please use YYYYMMDD (e.g., 18680903).'

        if not error:

            cities, total_matches = get_paginated_cities(

                selected_country, 

                selected_state, 

                page, 

                user_element, 

                user_const,

                sort_order

            )

    elif request.method == 'GET' and (request.args.get('birth_date') or birth_date):

        birth_date = request.args.get('birth_date', birth_date)

        selected_country = request.args.get('country', selected_country)

        selected_state = request.args.get('state_country', selected_state)

        page = int(request.args.get('page', page))

        sort_order = request.args.get('sort', sort_order)

        if selected_country != 'All' and selected_country not in small_countries:

            states = ['All'] + country_to_states.get(selected_country, [])

        elif selected_country in small_countries:

            states = ['All']

        if not validate_date(birth_date):

            error = 'Invalid date format. Please use YYYYMMDD (e.g., 19900515).'

        else:

            user_const, user_element = get_constellation_and_element(birth_date, for_user=True)

            if not user_const:

                error = 'Invalid birth date. Please use YYYYMMDD (e.g., 19900515).'

        if not error:

            cities, total_matches = get_paginated_cities(

                selected_country, 

                selected_state, 

                page, 

                user_element, 

                user_const,

                sort_order

            )

    print(f"Request: {request.method}, Page: {page}, Sort: {sort_order}, Birth Date: {birth_date}")

    return render_template('lucky_city_page.html', 

        cities=cities, 

        page=page, 

        total_matches=total_matches,

        birth_date=birth_date, 

        selected_country=selected_country, 

        selected_state=selected_state,

        manual_city=manual_city, 

        manual_date=manual_date, 

        manual_result=manual_result,

        countries=countries, 

        states=states, 

        user_const=user_const, 

        user_element=user_element,

        error=error,

        country_to_states=country_to_states, 

        small_countries=small_countries,

        sort_order=sort_order

    )



# Debug route

@app.route('/routes')

def show_routes():

    routes = []

    for rule in app.url_map.iter_rules():

        routes.append({

            'endpoint': rule.endpoint,

            'methods': list(rule.methods),

            'rule': str(rule)

        })

    return jsonify(routes)



if __name__ == '__main__':

    app.run(debug=True, host='127.0.0.1', port=5000)
