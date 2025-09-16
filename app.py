```python
import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar
from datetime import datetime
import hashlib

app = Flask(__name__)
CORS(app)

# 公历版 28 星宿查询表（已翻译为英文）
LUNAR_MANSIONS = [
    ["The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well"],
    ["The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost"],
    ["The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow"],
    ["The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star"],
    ["The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net"],
    ["The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings"],
    ["The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot"],
    ["The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn"],
    ["The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck"],
    ["The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root"],
    ["The Three Stars", "The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room"],
    ["The Well", "The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart"],
    ["The Ghost", "The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail"],
    ["The Willow", "The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket"],
    ["The Star", "The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper"],
    ["The Extended Net", "The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox"],
    ["The Wings", "The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl"],
    ["The Chariot", "The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void"],
    ["The Horn", "The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop"],
    ["The Neck", "The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment"],
    ["The Root", "The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall"],
    ["The Room", "The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs"],
    ["The Heart", "The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond"],
    ["The Tail", "The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach"],
    ["The Winnowing Basket", "The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades"],
    ["The Dipper", "The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net"],
    ["The Ox", "The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak"],
    ["The Girl", "The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars"],
    ["The Void", "The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well"],
    ["The Rooftop", "The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost"],
    ["The Encampment", "The Wall", "The Legs", "The Bond", "The Stomach", "The Pleiades", "The Net", "The Beak", "The Three Stars", "The Well", "The Ghost", "The Willow"]
]

# 星宿描述
lunar_mansions_descriptions = {
    "The Horn": "The beacon of ambition, igniting your path to success.",
    "The Neck": "The guardian of balance, harmonizing your cosmic journey.",
    "The Root": "The anchor of wisdom, grounding your soul in truth.",
    "The Room": "The haven of growth, opening doors to new beginnings.",
    "The Heart": "The star of passion, guiding your heart to cosmic love.",
    "The Tail": "The spark of transformation, leading you to renewal.",
    "The Winnowing Basket": "The weave of abundance, attracting prosperity and joy.",
    "The Dipper": "The ladle of destiny, pouring clarity into your fate.",
    "The Ox": "The pillar of strength, carrying you through challenges.",
    "The Girl": "The muse of grace, inspiring beauty in your actions.",
    "The Void": "The void of potential, inviting infinite possibilities.",
    "The Rooftop": "The flame of courage, empowering you to face fears.",
    "The Encampment": "The fortress of stability, shielding your dreams.",
    "The Wall": "The barrier of protection, safeguarding your spirit.",
    "The Legs": "The stride of progress, propelling you toward goals.",
    "The Bond": "The tie of connection, uniting you with cosmic allies.",
    "The Stomach": "The core of resilience, fueling your inner strength.",
    "The Pleiades": "The cluster of insight, illuminating hidden truths.",
    "The Net": "The web of opportunity, capturing luck in your path.",
    "The Beak": "The point of precision, sharpening your focus and will.",
    "The Three Stars": "The triad of harmony, balancing mind, body, soul.",
    "The Well": "The source of vitality, nourishing your cosmic energy.",
    "The Ghost": "The whisper of ancestors, guiding with ancient wisdom.",
    "The Willow": "The branch of flexibility, bending with life's flow.",
    "The Star": "The light of destiny, shining on your true purpose.",
    "The Extended Net": "The reach of ambition, expanding your cosmic horizon.",
    "The Wings": "The flight of freedom, soaring to new heights.",
    "The Chariot": "The vehicle of progress, driving you to victory."
}

def get_fallback_mansion(date_str):
    """对于无效日期，返回一个基于哈希的确定性星宿"""
    hash_object = hashlib.sha256(date_str.encode())
    hash_value = int(hash_object.hexdigest(), 16)
    mansion_index = hash_value % 28
    mansion_name = list(lunar_mansions_descriptions.keys())[mansion_index]
    gunicorn_logger.warning(f"Using fallback mansion for {date_str}: {mansion_name}")
    return mansion_name

def get_lunar_mansion(year, month, day):
    """根据公历日期返回对应的28星宿名称"""
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    try:
        # 验证日期
        datetime(year, month, day)
        month_idx = month - 1
        day_idx = day - 1
        
        # 检查月份天数
        if month in [4, 6, 9, 11] and day > 30:
            gunicorn_logger.error(f"Invalid day {day} for month {month}")
            return get_fallback_mansion(date_str)
        if month == 2:
            is_leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
            if (is_leap_year and day > 29) or (not is_leap_year and day > 28):
                gunicorn_logger.error(f"Invalid day {day} for February in year {year}")
                return get_fallback_mansion(date_str)
        if day_idx < 0 or day_idx > 30 or month_idx < 0 or month_idx > 11:
            gunicorn_logger.error(f"Out of range: month={month}, day={day}")
            return get_fallback_mansion(date_str)
        
        # 确保访问安全
        if day_idx >= len(LUNAR_MANSIONS) or month_idx >= len(LUNAR_MANSIONS[0]):
            gunicorn_logger.error(f"Index out of range: day_idx={day_idx}, month_idx={month_idx}")
            return get_fallback_mansion(date_str)
        
        mansion = LUNAR_MANSIONS[day_idx][month_idx]
        if not mansion or mansion not in lunar_mansions_descriptions:
            gunicorn_logger.error(f"Invalid mansion: {mansion}")
            return get_fallback_mansion(date_str)
        
        gunicorn_logger.debug(f"Date: {date_str}, Month: {month}, Day: {day}, Mansion: {mansion}")
        return mansion
    except Exception as e:
        gunicorn_logger.error(f"Error processing date {date_str}: {str(e)}")
        return get_fallback_mansion(date_str)

# 健康检查端点
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

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

# Five Elements mapping for stems
five_elements = {
    '甲': 'Wood', '乙': 'Wood', '丙': 'Fire', '丁': 'Fire', 
    '戊': 'Earth', '己': 'Earth', '庚': 'Metal', '辛': 'Metal', 
    '壬': 'Water', '癸': 'Water'
}

# Joy Directions based on Five Elements with angles
joy_directions = {
    'Wood': {'joy': 'North (Water)', 'angle': 0},
    'Fire': {'joy': 'East (Wood)', 'angle': 90},
    'Earth': {'joy': 'South (Fire)', 'angle': 180},
    'Metal': {'joy': 'South (Earth)', 'angle': 145},
    'Water': {'joy': 'West (Metal)', 'angle': 270}
}

# 特殊日期修正（临时解决方案）
DATE_CORRECTIONS = {
    (1976, 12, 3): {'lunar_year': 1976, 'lunar_month': 11, 'lunar_day': 3}
}

# 八字计算端点
@app.route('/calculate', methods=['GET'])
def calculate():
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    received_hour = request.args.get('hour')
    received_minute = request.args.get('minute')
    received_timezone = request.args.get('timezone', '8')
    
    gunicorn_logger.debug(
        f"Received GET /calculate with params: year={received_year}, month={received_month}, day={received_day}, "
        f"hour={received_hour}, minute={received_minute}, timezone={received_timezone}"
    )

    try:
        if not (received_year and received_month and received_day):
            error_msg = 'Missing required parameters: year, month, or day cannot be empty'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        year = int(received_year)
        month = int(received_month)
        day = int(received_day)
        
        if year < 1900 or year > 2025:
            error_msg = 'Year must be between 1900 and 2025'
            return jsonify({'error': error_msg}), 400
        if month < 1 or month > 12:
            error_msg = 'Month must be between 1 and 12'
            return jsonify({'error': error_msg}), 400
        if day < 1 or day > 31:
            error_msg = 'Day must be between 1 and 31'
            return jsonify({'error': error_msg}), 400

        try:
            datetime(year, month, day)
        except ValueError as e:
            error_msg = f'Invalid date: {str(e)}'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        hour = None
        minute = None
        if received_hour:
            try:
                hour = int(received_hour)
                if hour < 0 or hour > 23:
                    raise ValueError("Hour out of range 0-23")
            except ValueError as e:
                error_msg = f'Invalid hour: {str(e)}'
                return jsonify({'error': error_msg}), 400
        if received_minute:
            try:
                minute = int(received_minute)
                if minute < 0 or minute > 59:
                    raise ValueError("Minute out of range 0-59")
            except ValueError as e:
                error_msg = f'Invalid minute: {str(e)}'
                return jsonify({'error': error_msg}), 400

        try:
            solar = Solar.fromYmd(year, month, day)
            lunar = solar.getLunar()
            if not lunar:
                error_msg = f"Failed to convert solar date {year}-{month:02d}-{day:02d} to lunar date"
                gunicorn_logger.error(error_msg)
                return jsonify({'error': error_msg}), 400
        except Exception as e:
            error_msg = f"Lunar conversion failed for {year}-{month:02d}-{day:02d}: {str(e)}"
            gunicorn_logger.error(error_msg, exc_info=True)
            return jsonify({'error': error_msg}), 400
        
        date_key = (year, month, day)
        if date_key in DATE_CORRECTIONS:
            lunar_year = DATE_CORRECTIONS[date_key]['lunar_year']
            lunar_month = DATE_CORRECTIONS[date_key]['lunar_month']
            lunar_day = DATE_CORRECTIONS[date_key]['lunar_day']
            gunicorn_logger.debug(f"Applied lunar date correction: {lunar_year}-{lunar_month:02d}-{lunar_day:02d}")
        else:
            lunar_year = lunar.getYear()
            lunar_month = lunar.getMonth()
            lunar_day = lunar.getDay()
        
        if not isinstance(lunar_day, int) or lunar_day < 1 or lunar_day > 31:
            error_msg = f"Invalid lunar day {lunar_day} for date {year}-{month:02d}-{day:02d}"
            gunicorn_logger.error(error_msg)
            return jsonify({
                'error': error_msg,
                'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                'bazi': 'Unknown',
                'lunar_mansion': "Unknown",
                'lunar_mansion_description': "Could not calculate lunar mansion for this date.",
                'angle': 0
            }), 400
        
        gunicorn_logger.debug(
            f"/calculate solar to lunar success: solar={year}-{month:02d}-{day:02d}, "
            f"lunar={lunar_year}-{lunar_month:02d}-{lunar_day:02d}"
        )

        try:
            ba = lunar.getEightChar()
            if not ba:
                error_msg = f"Failed to get Eight Characters (BaZi) for lunar date {lunar_year}-{lunar_month:02d}-{lunar_day:02d}"
                gunicorn_logger.error(error_msg)
                return jsonify({
                    'error': error_msg,
                    'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                    'bazi': 'Unknown',
                    'lunar_mansion': "Unknown",
                    'lunar_mansion_description': "Could not calculate lunar mansion for this date.",
                    'angle': 0
                }), 400
        except Exception as e:
            error_msg = f"BaZi calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}"
            gunicorn_logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': error_msg,
                'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                'bazi': 'Unknown',
                'lunar_mansion': "Unknown",
                'lunar_mansion_description': "Could not calculate lunar mansion for this date.",
                'angle': 0
            }), 400
        
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        
        for i, (gan, zhi) in enumerate(zip(gans, zhis)):
            if not gan or not zhi:
                error_msg = f"Invalid BaZi component at index {i}: gan={gan}, zhi={zhi}"
                gunicorn_logger.error(error_msg)
                return jsonify({
                    'error': error_msg,
                    'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                    'bazi': 'Unknown',
                    'lunar_mansion': "Unknown",
                    'lunar_mansion_description': "Could not calculate lunar mansion for this date.",
                    'angle': 0
                }), 400
        
        bazi = [f"{heavenly_stems.get(gan, 'Unknown')}{earthly_branches.get(zhi, 'Unknown')}" for gan, zhi in zip(gans, zhis)]
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")

        lunar_mansion = get_lunar_mansion(year, month, day)
        if not lunar_mansion or lunar_mansion not in lunar_mansions_descriptions:
            gunicorn_logger.error(f"Invalid lunar mansion: {lunar_mansion}, falling back")
            lunar_mansion = get_fallback_mansion(f"{year:04d}-{month:02d}-{day:02d}")
        
        lunar_mansion_desc = lunar_mansions_descriptions.get(lunar_mansion, "No description available.")
        
        day_master = gans[2]
        element = five_elements.get(day_master, 'Unknown')
        original_angle = joy_directions.get(element, {'angle': 0})['angle']

        try:
            benchmark_offset = 8.0
            user_offset = float(received_timezone)
            diff_hours = user_offset - benchmark_offset
            adjustment = diff_hours * 15
            angle = round(original_angle + adjustment, 2)
            angle = angle % 360
            if angle < 0:
                angle += 360
        except Exception as e:
            gunicorn_logger.error(f"Timezone adjustment failed: {str(e)}")
            angle = original_angle

        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems.get(day_master, 'Unknown')}, element={element}, "
            f"original_angle={original_angle}, adjusted_angle={angle}, lunar_mansion={lunar_mansion}"
        )

        return jsonify({
            'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
            'bazi': ' '.join(bazi),
            'lunar_mansion': lunar_mansion,
            'lunar_mansion_description': lunar_mansion_desc,
            'angle': angle
        })

    except Exception as e:
        error_msg = f'Calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}", exc_info=True)
        return jsonify({
            'error': error_msg,
            'lunar_date': 'Unknown',
            'bazi': 'Unknown',
            'lunar_mansion': "Unknown",
            'lunar_mansion_description': "Could not calculate lunar mansion for this date.",
            'angle': 0
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
```
