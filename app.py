import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 28星宿及其描述
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

# 星宿英文翻译
CONSTELLATION_TRANSLATIONS = {
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

def get_constellation_and_element(year, month, day):
    """根据公历日期计算对应的28星宿和元素"""
    try:
        # 创建公历对象并转换为农历
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        if not lunar:
            gunicorn_logger.error(f"Failed to convert solar date {year}-{month:02d}-{day:02d} to lunar date")
            return None, None
        
        lunar_day = lunar.getDay()
        gunicorn_logger.debug(f"Retrieved lunar_day: {lunar_day} for date {year}-{month:02d}-{day:02d}")
        
        # 确保 lunar_day 是有效的整数
        if not isinstance(lunar_day, int) or lunar_day < 1 or lunar_day > 31:
            gunicorn_logger.error(f"Invalid lunar_day: {lunar_day} for date {year}-{month:02d}-{day:02d}")
            return None, None
        
        # 计算星宿索引
        constellation_idx = (lunar_day - 1) % 28
        constellation = CONSTELLATIONS[constellation_idx][0]
        element = CONSTELLATIONS[constellation_idx][2]
        # 返回翻译后的星宿名称
        translated = CONSTELLATION_TRANSLATIONS.get(constellation, constellation)
        gunicorn_logger.debug(f"Calculated constellation: {translated}, element: {element} for lunar_day: {lunar_day}")
        return translated, element
    except Exception as e:
        gunicorn_logger.error(f"Error calculating constellation for date {year}-{month:02d}-{day:02d}: {str(e)}", exc_info=True)
        return None, None

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
        # 参数校验
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

        # 验证日期有效性
        try:
            datetime(year, month, day)
        except ValueError as e:
            error_msg = f'Invalid date: {str(e)}'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # 处理可选的时间参数
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

        # 创建公历对象并转换为农历
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
        
        lunar_year = lunar.getYear()
        lunar_month = lunar.getMonth()
        lunar_day = lunar.getDay()
        
        # 验证农历日期有效性
        if not isinstance(lunar_day, int) or lunar_day < 1 or lunar_day > 31:
            error_msg = f"Invalid lunar day {lunar_day} for date {year}-{month:02d}-{day:02d}"
            gunicorn_logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        gunicorn_logger.debug(
            f"/calculate solar to lunar success: solar={year}-{month:02d}-{day:02d}, "
            f"lunar={lunar_year}-{lunar_month:02d}-{lunar_day:02d}"
        )

        # 获取八字
        try:
            ba = lunar.getEightChar()
            if not ba:
                error_msg = f"Failed to get Eight Characters (BaZi) for lunar date {lunar_year}-{lunar_month:02d}-{lunar_day:02d}"
                gunicorn_logger.error(error_msg)
                return jsonify({'error': error_msg}), 400
        except Exception as e:
            error_msg = f"BaZi calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}"
            gunicorn_logger.error(error_msg, exc_info=True)
            return jsonify({'error': error_msg}), 400
        
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        
        for i, (gan, zhi) in enumerate(zip(gans, zhis)):
            if not gan or not zhi:
                raise ValueError(f"Invalid BaZi component at index {i}: gan={gan}, zhi={zhi}")
        
        # 生成八字英文标识
        bazi = [f"{heavenly_stems[gan]}{earthly_branches[zhi]}" for gan, zhi in zip(gans, zhis)]
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")

        # 计算28星宿
        lunar_mansion, _ = get_constellation_and_element(year, month, day)
        # 如果计算失败，使用默认值
        if not lunar_mansion:
            lunar_mansion = "Unknown"
            lunar_mansion_desc = "Could not calculate lunar mansion for this date."
        else:
            lunar_mansion_desc = lunar_mansions_descriptions.get(lunar_mansion, "No description available.")
        
        # 日主、五行、幸运方向计算
        day_master = gans[2]
        element = five_elements[day_master]
        original_angle = joy_directions[element]['angle']

        # 时区调整
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
            angle = original_angle  # 使用原始角度作为后备

        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems[day_master]}, element={element}, "
            f"original_angle={original_angle}, adjusted_angle={angle}, lunar_mansion={lunar_mansion}"
        )

        # 返回结果
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
        return jsonify({'error': error_msg}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
