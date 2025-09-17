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
earthly_branches_elements = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood', '辰': 'Earth', '巳': 'Fire',
    '午': 'Fire', '未': 'Earth', '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water'
}
joy_directions = {
    'Wood': {'base_angle': 0},
    'Fire': {'base_angle': 90},
    'Earth': {'base_angle': 180},
    'Metal': {'base_angle': 145},
    'Water': {'base_angle': 270}
}
mansion_personalities = [
    "Charismatic leaders who ignite projects with vision and drive.",
    "Resilient souls with unwavering strength and principles.",
    "Stable anchors providing security and grounding.",
    "Harmonious diplomats creating balanced environments.",
    "Wise hearts with deep emotional intelligence.",
    "Collaborative team players thriving in unity.",
    "Expressive communicators spreading enthusiasm.",
    "Transformative seekers of higher meaning.",
    "Diligent workers achieving goals through persistence.",
    "Creative observers crafting beauty with care.",
    "Introspective sages offering profound insights.",
    "Cautious protectors anticipating challenges.",
    "Adventurous explorers building communities.",
    "Scholarly keepers of culture and tradition.",
    "Innovative thinkers devising generous solutions.",
    "Generous unifiers providing warmth and support.",
    "Prosperous nurturers fostering growth.",
    "Confident stars leading with charisma.",
    "Methodical achievers reaping rewards.",
    "Perceptive advisors assessing with clarity.",
    "Analytical minds distinguishing truth.",
    "Caring providers of emotional sustenance.",
    "Empathetic intuitives understanding hidden truths.",
    "Graceful adapters managing with elegance.",
    "Optimistic creators spreading hope.",
    "Expansive visionaries embracing others.",
    "Free-spirited innovators bringing new ideas.",
    "Compassionate healers helping others forward."
]
mystic_descriptions = {
    1: "A spark of unity ignites your unique path to creation.",
    2: "Duality’s dance harmonizes your heart and mind.",
    3: "Creativity’s triad weaves inspiration into action.",
    4: "Stability’s foundation grounds your dreams.",
    5: "Adventure’s pulse propels you to discoveries.",
    6: "Harmony’s embrace nurtures love and balance.",
    7: "Intuition’s whisper guides you to profound truths.",
    8: "Abundance’s cycle manifests your aspirations.",
    9: "Wisdom’s beacon illuminates your path.",
    10: "Completion’s circle empowers your purpose.",
    11: "Enlightenment’s gateway opens your spirit.",
    12: "Growth’s rhythm aligns you with the universe.",
    13: "Transformation’s flame sparks renewal.",
    14: "Connection’s bridge unites you with allies.",
    15: "Courage’s surge emboldens your opportunities.",
    16: "Resilience’s pillar anchors your strength.",
    17: "Clarity’s star shines on your purpose.",
    18: "Vitality’s tide floods your spirit with energy.",
    19: "Inspiration’s dawn awakens bold visions.",
    20: "Protection’s shield guards your dreams.",
    21: "Innovation’s spark ignites new paths.",
    22: "Destiny’s architect builds your legacy.",
    23: "Freedom’s pulse liberates your spirit.",
    24: "Joy’s wellspring nourishes your soul.",
    25: "Opportunity’s thread weaves luck and success.",
    26: "Passion’s flame fuels your dreams.",
    27: "Truth’s mirror reflects your strength.",
    28: "Progress’s current carries you to your goals."
}

# 健康检查端点
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

def get_mystic_description(day):
    try:
        day = int(day)
        return mystic_descriptions.get(day, "A cosmic whisper guides your journey.")
    except (ValueError, TypeError):
        return "A cosmic whisper guides your journey."

def get_element_interaction(gan, zhi):
    gan_element = five_elements.get(gan, 'Unknown')
    zhi_element = earthly_branches_elements.get(zhi, 'Unknown')
    if gan_element == 'Unknown' or zhi_element == 'Unknown':
        return f"{heavenly_stems[gan]}{earthly_branches[zhi]}"
    return f"{heavenly_stems[gan]}{earthly_branches[zhi]}: {gan_element} meets {zhi_element}"

@app.route('/calculate', methods=['GET'])
def calculate():
    params = {
        'year': request.args.get('year'),
        'month': request.args.get('month'),
        'day': request.args.get('day'),
        'timezone': request.args.get('timezone', 8.0)
    }
    gunicorn_logger.debug(f"Received params: {params}")

    try:
        if not all([params['year'], params['month'], params['day']]):
            return jsonify({'error': 'Year, month, and day are required'}), 400

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

        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        if not lunar:
            return jsonify({'error': 'Failed to convert to lunar calendar'}), 400

        lunar_day = lunar.getDay()
        mansion_index = (lunar_day - 1) % 28
        personality = mansion_personalities[mansion_index]

        ba = lunar.getEightChar()
        if not ba:
            return jsonify({'error': 'Failed to calculate Cosmic Blueprint'}), 400
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        for g, z in zip(gans, zhis):
            if not g or not z:
                return jsonify({'error': 'Invalid Cosmic Blueprint components'}), 400
        bazi_interactions = [get_element_interaction(g, z) for g, z in zip(gans, zhis)]

        day_master = gans[2]
        element = five_elements.get(day_master, 'Unknown')
        if element == 'Unknown':
            return jsonify({'error': 'Failed to determine element'}), 400

        base_angle = joy_directions[element]['base_angle']
        dynamic_offset = random.randint(-10, 10)
        try:
            benchmark_offset = 8.0
            user_offset = float(params['timezone'])
            diff_hours = user_offset - benchmark_offset
            timezone_adjustment = diff_hours * 15
            angle = (base_angle + dynamic_offset + timezone_adjustment) % 360
        except:
            angle = (base_angle + dynamic_offset) % 360

        mystic_desc = get_mystic_description(day)

        return jsonify({
            'solar_date': f"{year}-{month:02d}-{day:02d}",
            'bazi': ', '.join(bazi_interactions),
            'personality': personality,
            'mystic_description': mystic_desc,
            'angle': round(angle, 2)
        })

    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        gunicorn_logger.error(error_msg)
        return jsonify({'error': error_msg}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)