import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Heavenly Stems (English mapping)
heavenly_stems = {
    '甲': 'Jia', '乙': 'Yi', '丙': 'Bing', '丁': 'Ding', 
    '戊': 'Wu', '己': 'Ji', '庚': 'Geng', '辛': 'Xin', 
    '壬': 'Ren', '癸': 'Gui'
}

# Earthly Branches (English mapping)
earthly_branches = {
    '子': 'Zi', '丑': 'Chou', '寅': 'Yin', '卯': 'Mao', 
    '辰': 'Chen', '巳': 'Si', '午': 'Wu', '未': 'Wei', 
    '申': 'Shen', '酉': 'You', '戌': 'Xu', '亥': 'Hai'
}

# Five Elements mapping
five_elements = {
    '甲': 'Wood', '乙': 'Wood', '丙': 'Fire', '丁': 'Fire', 
    '戊': 'Earth', '己': 'Earth', '庚': 'Metal', '辛': 'Metal', 
    '壬': 'Water', '癸': 'Water'
}

# Five Elements relationships
element_relations = {
    'Wood': {'produced_by': 'Water', 'produces': 'Fire'},
    'Fire': {'produced_by': 'Wood', 'produces': 'Earth'},
    'Earth': {'produced_by': 'Fire', 'produces': 'Metal'},
    'Metal': {'produced_by': 'Earth', 'produces': 'Water'},
    'Water': {'produced_by': 'Metal', 'produces': 'Wood'}
}

# Joy Directions based on Five Elements with angles
joy_directions = {
    'Wood': {'joy': 'North (Water)', 'angle': 0},
    'Fire': {'joy': 'East (Wood)', 'angle': 90},
    'Earth': {'joy': 'South (Fire)', 'angle': 180},
    'Metal': {'joy': 'South (Earth)', 'angle': 180},
    'Water': {'joy': 'West (Metal)', 'angle': 270}
}

# Direction mapping
direction_mapping = {
    'North': 'North',
    'East': 'East',
    'South': 'South',
    'West': 'West'
}

@app.route('/calculate', methods=['GET'])
def calculate():
    year = int(request.args.get('year', 0))
    month = int(request.args.get('month', 0))
    day = int(request.args.get('day', 0))
    if not (year and month and day):
        return jsonify({'error': 'Missing year, month, or day'}), 400
    try:
        # Convert solar to lunar
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        
        # Get BaZi
        ba = lunar.getEightChar()
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        
        # Day Master and Element
        day_master = gans[2]
        element = five_elements[day_master]
        joy_direction = joy_directions[element]['joy']
        angle = joy_directions[element]['angle']
        
        # Convert to English
        bazi = [f"{heavenly_stems[g]}{earthly_branches[z]}" for g, z in zip(gans, zhis)]
        
        # Simplified explanation
        relation = element_relations[element]
        direction = joy_direction.split(' ')[0]
        direction_english = direction_mapping[direction]
        explanation = f"Your Day Master is {element}. {element_english} supports {element}, so your lucky direction is {direction_english}."
        
        return jsonify({
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi': ' '.join(bazi),
            'day_master': heavenly_stems[day_master],
            'element': element,
            'joy_direction': joy_direction,
            'angle': angle,
            'explanation': explanation
        })
    except Exception as e:
        return jsonify({'error': f'Calculation failed: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)