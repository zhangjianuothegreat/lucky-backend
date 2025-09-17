import logging
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar
from datetime import datetime

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

# 基础数据
heavenly_stems = {
    '甲': 'Jia', '乙': 'Yi', '丙': 'Bing', '丁': 'Ding', '戊': 'Wu',
    '己': 'Ji', '庚': 'Geng', '辛': 'Xin', '壬': 'Ren', '癸': 'Gui'
}
earthly_branches = {
    '子': 'Zi', '丑': 'Chou', '寅': 'Yin', '卯': 'Mao', '辰': 'Chen', '巳': 'Si',
    '午': 'Wu', '未': 'Wei', '申': 'Shen', '酉': 'You', '戌': 'Xu', '亥': 'Hai'
}
five_elements = {
    '甲': 'Wood', '乙': 'Wood', '丙': 'Fire', '丁': 'Fire', '戊': 'Earth',
    '己': 'Earth', '庚': 'Metal', '辛': 'Metal', '壬': 'Water', '癸': 'Water'
}
joy_directions = {
    'Wood': {'joy': 'North', 'base_angle': 0},
    'Fire': {'joy': 'East', 'base_angle': 90},
    'Earth': {'joy': 'South', 'base_angle': 180},
    'Metal': {'joy': 'South', 'base_angle': 145},
    'Water': {'joy': 'West', 'base_angle': 270}
}
direction_mapping = {
    'North': 'North', 'East': 'East', 'South': 'South', 'West': 'West'
}
lunar_mansions = [
    "角木蛟", "亢金龙", "氐土貉", "房日兔", "心月狐", "尾火虎", "箕水豹",
    "斗木獬", "牛金牛", "女土蝠", "虚日鼠", "危月燕", "室火猪", "壁水貐",
    "奎木狼", "娄金狗", "胃土雉", "昴日鸡", "毕月乌", "觜火猴", "参水猿",
    "井木犴", "鬼金羊", "柳土獐", "星日马", "张月鹿", "翼火蛇", "轸水蚓"
]
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

# 健康检查端点
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

def get_mystic_description(day):
    try:
        day = int(day)
        return mystic_descriptions.get(day, "No cosmic message for this day.")
    except (ValueError, TypeError):
        return "Could not retrieve cosmic message."

@app.route('/calculate', methods=['GET'])
def calculate():
    # 获取参数
    params = {
        'year': request.args.get('year'),
        'month': request.args.get('month'),
        'day': request.args.get('day'),
        'hour': request.args.get('hour'),
        'minute': request.args.get('minute'),
        'timezone': request.args.get('timezone', '8')
    }
    gunicorn_logger.debug(f"Received params: {params}")

    try:
        # 参数验证
        if not all([params['year'], params['month'], params['day']]):
            return jsonify({'error': 'Year, month and day are required'}), 400

        # 基础日期验证
        year = int(params['year'])
        month = int(params['month'])
        day = int(params['day'])
        if year < 1900 or year > 2025:
            return jsonify({'error': 'Year must be 1900-2025'}), 400
        if month < 1 or month > 12:
            return jsonify({'error': 'Month must be 1-12'}), 400
        if day < 1 or day > 31:
            return jsonify({'error': 'Day must be 1-31'}), 400
        try:
            datetime(year, month, day)
        except ValueError:
            return jsonify({'error': 'Invalid date (e.g., February 30 is invalid)'}), 400

        # 时间验证
        hour = int(params['hour']) if params['hour'] else None
        minute = int(params['minute']) if params['minute'] else None
        if hour is not None and (hour < 0 or hour > 23):
            return jsonify({'error': 'Hour must be 0-23'}), 400
        if minute is not None and (minute < 0 or minute > 59):
            return jsonify({'error': 'Minute must be 0-59'}), 400

        # 农历转换
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        if not lunar:
            return jsonify({'error': 'Failed to convert to lunar calendar'}), 400

        # 28星宿计算（来自grok版本）
        lunar_day = lunar.getDay()
        mansion_index = (lunar_day - 1) % 28
        mansion = lunar_mansions[mansion_index]

        # 八字计算
        ba = lunar.getEightChar()
        if not ba:
            return jsonify({'error': 'Failed to calculate Bazi'}), 400
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        for g, z in zip(gans, zhis):
            if not g or not z:
                return jsonify({'error': 'Invalid Bazi components'}), 400
        bazi = [f"{heavenly_stems[g]}{earthly_branches[z]}" for g, z in zip(gans, zhis)]

        # 方向计算（融合动态偏移+时区调整）
        day_master = gans[2]
        element = five_elements.get(day_master, 'Unknown')
        if element == 'Unknown':
            return jsonify({'error': 'Failed to determine element'}), 400
        
        base_angle = joy_directions[element]['base_angle']
        dynamic_offset = random.randint(-10, 10)  # grok的动态偏移
        try:
            # 原版本的时区调整
            benchmark_offset = 8.0
            user_offset = float(params['timezone'])
            diff_hours = user_offset - benchmark_offset
            timezone_adjustment = diff_hours * 15
            angle = (base_angle + dynamic_offset + timezone_adjustment) % 360
        except:
            angle = (base_angle + dynamic_offset) % 360

        # 宇宙密码（原版本）
        mystic_desc = get_mystic_description(day)

        return jsonify({
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi': ' '.join(bazi),
            'mansion': mansion,  # 28星宿放在八字和宇宙密码之间
            'mystic_description': mystic_desc,
            'joy_direction': direction_mapping[joy_directions[element]['joy']],
            'angle': round(angle, 2)
        })

    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        gunicorn_logger.error(error_msg)
        return jsonify({'error': error_msg}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
