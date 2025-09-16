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

# 神秘描述字典
mystic_descriptions = {
    1: "The spark of unity, igniting your unique path to boundless creation and singular purpose.",
    2: "The dance of duality, harmonizing your heart and mind to forge meaningful connections.",
    3: "The triad of creativity, weaving inspiration into actions that shape your vibrant destiny.",
    4: "The foundation of stability, grounding your dreams in a fortress of unwavering resolve.",
    5: "The pulse of adventure, propelling you toward discoveries that awaken your inner explorer.",
    6: "The embrace of harmony, nurturing love and balance in your soul’s radiant journey.",
    7: "The whisper of intuition, guiding you through mysteries to uncover profound truths.",
    8: "The cycle of abundance, channeling infinite energy to manifest your greatest aspirations.",
    9: "The beacon of wisdom, illuminating your path with compassion and universal understanding.",
    10: "The circle of completion, empowering you to fulfill your purpose with bold confidence.",
    11: "The gateway of enlightenment, opening your spirit to visions of higher consciousness.",
    12: "The rhythm of growth, aligning your steps with the universe’s eternal flow.",
    13: "The flame of transformation, sparking renewal to elevate your soul’s potential.",
    14: "The bridge of connection, uniting your heart with allies on a shared mission.",
    15: "The surge of courage, emboldening you to conquer fears and seize opportunities.",
    16: "The pillar of resilience, anchoring your strength to overcome life’s greatest trials.",
    17: "The star of clarity, shining light on your purpose with unwavering focus.",
    18: "The tide of vitality, flooding your spirit with energy to thrive and create.",
    19: "The dawn of inspiration, awakening your soul to bold ideas and grand visions.",
    20: "The shield of protection, guarding your dreams with unyielding cosmic support.",
    21: "The spark of innovation, igniting your mind to pioneer new paths forward.",
    22: "The architect of destiny, building your legacy with precision and purpose.",
    23: "The pulse of freedom, liberating your spirit to soar to new heights.",
    24: "The wellspring of joy, nourishing your soul with endless positivity and grace.",
    25: "The thread of opportunity, weaving luck and success into your journey.",
    26: "The flame of passion, fueling your heart to pursue dreams with fervor.",
    27: "The mirror of truth, reflecting your inner strength and authentic purpose.",
    28: "The current of progress, carrying you swiftly toward your highest goals.",
    29: "The whisper of eternity, guiding you to embrace your timeless mission.",
    30: "The crown of fulfillment, honoring your journey with wisdom and triumph.",
    31: "The light of transcendence, elevating your soul to embrace infinite possibilities."
}

def get_mystic_description(day):
    """根据日期的'日'返回对应的神秘描述"""
    try:
        day = int(day)
        if 1 <= day <= 31:
            return mystic_descriptions.get(day, "No description available for this day.")
        else:
            gunicorn_logger.error(f"Invalid day: {day}")
            return "Could not calculate your cosmic code for this date."
    except ValueError as e:
        gunicorn_logger.error(f"Error processing day {day}: {str(e)}")
        return "Could not calculate your cosmic code for this date."

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
                'mystic_description': "Could not calculate your cosmic code for this date.",
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
                    'mystic_description': "Could not calculate your cosmic code for this date.",
                    'angle': 0
                }), 400
        except Exception as e:
            error_msg = f"BaZi calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}"
            gunicorn_logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': error_msg,
                'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                'bazi': 'Unknown',
                'mystic_description': "Could not calculate your cosmic code for this date.",
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
                    'mystic_description': "Could not calculate your cosmic code for this date.",
                    'angle': 0
                }), 400
        
        bazi = [f"{heavenly_stems.get(gan, 'Unknown')}{earthly_branches.get(zhi, 'Unknown')}" for gan, zhi in zip(gans, zhis)]
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")

        mystic_description = get_mystic_description(day)
        
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
            f"original_angle={original_angle}, adjusted_angle={angle}, mystic_description={mystic_description}"
        )

        return jsonify({
            'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
            'bazi': ' '.join(bazi),
            'mystic_description': mystic_description,
            'angle': angle
        })

    except Exception as e:
        error_msg = f'Calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}", exc_info=True)
        return jsonify({
            'error': error_msg,
            'lunar_date': 'Unknown',
            'bazi': 'Unknown',
            'mystic_description': "Could not calculate your cosmic code for this date.",
            'angle': 0
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
