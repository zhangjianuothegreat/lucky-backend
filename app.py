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

# 星宿英文翻译
CONSTELLATION_TRANSLATIONS = {
    '角宿': 'The Horn', '亢宿': 'The Neck', '氐宿': 'The Root',
    '房宿': 'The Room', '心宿': 'The Heart', '尾宿': 'The Tail',
    '箕宿': 'The Winnowing Basket', '斗宿': 'The Dipper', '牛宿': 'The Ox',
    '女宿': 'The Girl', '虚宿': 'The Void', '危宿': 'The Rooftop',
    '室宿': 'The Encampment', '壁宿': 'The Wall', '奎宿': 'The Legs',
    '娄宿': 'The Bond', '胃宿': 'The Stomach', '昴宿': 'The Pleiades',
    '毕宿': 'The Net', '觜宿': 'The Beak', '参宿': 'The Three Stars',
    '井宿': 'The Well', '鬼宿': 'The Ghost', '柳宿': 'The Willow',
    '星宿': 'The Star', '张宿': 'The Extended Net', '翼宿': 'The Wings',
    '轸宿': 'The Chariot'
}

# 二十八星宿表格（30行 x 12列，行对应日期1-30，列对应月份1-12）
CONSTELLATION_TABLE = [
    ["虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿"],
    ["危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿"],
    ["室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿"],
    ["壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿"],
    ["奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿"],
    ["娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿"],
    ["胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿"],
    ["昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿"],
    ["毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿"],
    ["觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿"],
    ["参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿"],
    ["井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿"],
    ["鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿"],
    ["柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿"],
    ["星宿", "翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿"],
    ["张宿", "轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿"],
    ["翼宿", "角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿"],
    ["轸宿", "亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿"],
    ["角宿", "氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿"],
    ["亢宿", "房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿"],
    ["氐宿", "心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿"],
    ["房宿", "尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿"],
    ["心宿", "箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿"],
    ["尾宿", "斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿"],
    ["箕宿", "牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿"],
    ["斗宿", "女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿"],
    ["牛宿", "虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿"],
    ["女宿", "危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿"],
    ["虚宿", "室宿", "奎宿", "胃宿", "毕宿", "参宿", "鬼宿", "星宿", "翼宿", "角宿", "氐宿", "心宿"],
    ["危宿", "壁宿", "娄宿", "昴宿", "觜宿", "井宿", "柳宿", "张宿", "轸宿", "亢宿", "房宿", "尾宿"]
]

# 特殊日期修正（临时解决方案）
DATE_CORRECTIONS = {
    (1976, 12, 3): {'lunar_year': 1976, 'lunar_month': 11, 'lunar_day': 3}
}

# 健康检查端点
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

# 八字和星宿计算端点
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
        
        # 检查是否有特殊日期修正
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
        
        # 验证农历日期有效性
        if not isinstance(lunar_month, int) or not isinstance(lunar_day, int) or lunar_month < 1 or lunar_month > 12 or lunar_day < 1 or lunar_day > 30:
            error_msg = f"Invalid lunar date: month={lunar_month}, day={lunar_day}"
            gunicorn_logger.error(error_msg)
            return jsonify({
                'error': error_msg,
                'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                'bazi': 'Unknown',
                'constellation': 'Invalid lunar date',
                'angle': 0
            }), 400
        
        gunicorn_logger.debug(
            f"/calculate solar to lunar success: solar={year}-{month:02d}-{day:02d}, "
            f"lunar={lunar_year}-{lunar_month:02d}-{lunar_day:02d}"
        )

        # 计算二十八星宿
        try:
            chinese_host = CONSTELLATION_TABLE[lunar_day - 1][lunar_month - 1]
            constellation = CONSTELLATION_TRANSLATIONS.get(chinese_host, 'Unknown')
            gunicorn_logger.debug(f"Constellation found: {chinese_host} -> {constellation}")
        except IndexError as e:
            constellation = 'Unknown'
            gunicorn_logger.error(f"IndexError in constellation table: {str(e)}, lunar_day={lunar_day}, lunar_month={lunar_month}")
        except Exception as e:
            constellation = 'Unknown'
            gunicorn_logger.error(f"Constellation calculation failed: {str(e)}")

        # 获取八字
        try:
            ba = lunar.getEightChar()
            if not ba:
                error_msg = f"Failed to get Eight Characters (BaZi) for lunar date {lunar_year}-{lunar_month:02d}-{lunar_day:02d}"
                gunicorn_logger.error(error_msg)
                return jsonify({
                    'error': error_msg,
                    'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                    'bazi': 'Unknown',
                    'constellation': constellation,
                    'angle': 0
                }), 400
        except Exception as e:
            error_msg = f"BaZi calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}"
            gunicorn_logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': error_msg,
                'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                'bazi': 'Unknown',
                'constellation': constellation,
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
                    'constellation': constellation,
                    'angle': 0
                }), 400
        
        # 生成八字英文标识
        bazi = [f"{heavenly_stems.get(gan, 'Unknown')}{earthly_branches.get(zhi, 'Unknown')}" for gan, zhi in zip(gans, zhis)]
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")

        # 日主、五行、幸运方向计算
        day_master = gans[2]
        element = five_elements.get(day_master, 'Unknown')
        original_angle = joy_directions.get(element, {'angle': 0})['angle']

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
            angle = original_angle

        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems.get(day_master, 'Unknown')}, element={element}, "
            f"original_angle={original_angle}, adjusted_angle={angle}"
        )

        # 返回结果
        return jsonify({
            'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
            'bazi': ' '.join(bazi),
            'constellation': constellation,
            'angle': angle
        })

    except Exception as e:
        error_msg = f'Calculation failed for {year}-{month:02d}-{day:02d}: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}", exc_info=True)
        return jsonify({
            'error': error_msg,
            'lunar_date': 'Unknown',
            'bazi': 'Unknown',
            'constellation': 'Unknown',
            'angle': 0
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
