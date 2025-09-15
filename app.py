import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# 健康检查端点（保留原有日志）
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')  # 健康检查日志
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

# Five Elements mapping for branches
branch_elements = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood', 
    '辰': 'Earth', '巳': 'Fire', '午': 'Fire', '未': 'Earth', 
    '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water'
}

# Adjectives for elements
element_adjectives = {
    'Wood': 'growth',
    'Fire': 'passion',
    'Earth': 'stability',
    'Metal': 'strength',
    'Water': 'flow'
}

def get_pillar_explanation(gan_element, zhi_element):
    adj1 = element_adjectives[gan_element]
    adj2 = element_adjectives[zhi_element]
    return f"{gan_element} meets {zhi_element}, a celestial blend of {adj1} and {adj2}."

# Joy Directions based on Five Elements with angles
joy_directions = {
    'Wood': {'joy': 'North (Water)', 'angle': 0},
    'Fire': {'joy': 'East (Wood)', 'angle': 90},
    'Earth': {'joy': 'South (Fire)', 'angle': 180},
    'Metal': {'joy': 'South (Earth)', 'angle': 145},
    'Water': {'joy': 'West (Metal)', 'angle': 270}
}

# 八字计算端点（添加日志，保留原有逻辑）
@app.route('/calculate', methods=['GET'])
def calculate():
    # 1. 记录请求参数日志（捕获是否接收到请求）
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    received_timezone = request.args.get('timezone', '8')  # 默认东八区
    gunicorn_logger.debug(
        f"Received GET /calculate with params: year={received_year}, month={received_month}, day={received_day}, timezone={received_timezone}"
    )

    try:
        # 原有参数校验逻辑
        year = int(received_year) if received_year else 0
        month = int(received_month) if received_month else 0
        day = int(received_day) if received_day else 0
        if not (year and month and day):
            error_msg = 'Missing year, month, or day'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")  # 记录参数缺失日志
            return jsonify({'error': error_msg}), 400

        # 原有农历转换逻辑
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        gunicorn_logger.debug(f"/calculate solar to lunar success: solar={year}-{month}-{day}, lunar={lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}")  # 记录农历转换结果

        # 原有八字计算逻辑
        ba = lunar.getEightChar()
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        bazi = [f"{heavenly_stems[g]}{earthly_branches[z]}" for g, z in zip(gans, zhis)]
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")  # 记录八字生成结果

        # 计算柱解释
        pillar_explanations = []
        for g, z in zip(gans, zhis):
            gan_element = five_elements[g]
            zhi_element = branch_elements[z]
            exp = get_pillar_explanation(gan_element, zhi_element)
            pillar_explanations.append(exp)

        # 原有日主、五行、幸运方向计算逻辑
        day_master = gans[2]
        element = five_elements[day_master]
        original_angle = joy_directions[element]['angle']

        # 时区调整逻辑（以东八区UTC+8为基准）
        benchmark_offset = 8.0
        user_offset = float(received_timezone)
        diff_hours = user_offset - benchmark_offset
        adjustment = diff_hours * 15
        angle = original_angle + adjustment
        angle = angle % 360
        if angle < 0:
            angle += 360

        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems[day_master]}, element={element}, original_angle={original_angle}, adjusted_angle={angle}"
        )  # 记录最终计算结果

        # 返回逻辑，移除不必要的字段
        return jsonify({
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi': ' '.join(bazi),
            'bazi_explanations': pillar_explanations,
            'angle': angle
        })

    # 原有异常捕获逻辑（添加错误日志）
    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}")  # 记录异常日志（用error级别更醒目）
        return jsonify({'error': error_msg}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
