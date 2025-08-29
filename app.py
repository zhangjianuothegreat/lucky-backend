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

# 八字计算端点（添加日志，保留原有逻辑）
@app.route('/calculate', methods=['GET'])
def calculate():
    # 1. 记录请求参数日志（捕获是否接收到请求）
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    gunicorn_logger.debug(
        f"Received GET /calculate with params: year={received_year}, month={received_month}, day={received_day}"
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

        # 原有日主、五行、幸运方向计算逻辑
        day_master = gans[2]
        element = five_elements[day_master]
        joy_direction = joy_directions[element]['joy']
        angle = joy_directions[element]['angle']
        relation = element_relations[element]
        direction = joy_direction.split(' ')[0]
        direction_english = direction_mapping[direction]
        explanation = f"Your Day Master is {element}. {relation['produced_by']} supports {element}, so your lucky direction is {direction_english}."
        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems[day_master]}, element={element}, joy_direction={joy_direction}, angle={angle}"
        )  # 记录最终计算结果

        # 原有返回逻辑
        return jsonify({
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi': ' '.join(bazi),
            'day_master': heavenly_stems[day_master],
            'element': element,
            'joy_direction': joy_direction,
            'angle': angle,
            'explanation': explanation
        })

    # 原有异常捕获逻辑（添加错误日志）
    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}")  # 记录异常日志（用error级别更醒目）
        return jsonify({'error': error_msg}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
