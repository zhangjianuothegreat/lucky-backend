import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar  # 确认导入正确
from datetime import datetime  # 提前导入datetime，避免重复导入

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

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

# Joy Directions based on Five Elements with angles (保持Metal为145°)
joy_directions = {
    'Wood': {'joy': 'North (Water)', 'angle': 0},
    'Fire': {'joy': 'East (Wood)', 'angle': 90},
    'Earth': {'joy': 'South (Fire)', 'angle': 180},
    'Metal': {'joy': 'South (Earth)', 'angle': 145},
    'Water': {'joy': 'West (Metal)', 'angle': 270}
}

# 八字计算端点（核心逻辑修改）
@app.route('/calculate', methods=['GET'])
def calculate():
    # 记录请求参数日志
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    received_hour = request.args.get('hour')  # 可选参数
    received_minute = request.args.get('minute')  # 可选参数
    received_timezone = request.args.get('timezone', '8')  # 默认东八区
    gunicorn_logger.debug(
        f"Received GET /calculate with params: year={received_year}, month={received_month}, day={received_day}, "
        f"hour={received_hour}, minute={received_minute}, timezone={received_timezone}"
    )

    try:
        # 参数校验 - 核心字段（严格校验非空和数值类型）
        if not (received_year and received_month and received_day):
            error_msg = 'Missing required parameters: year, month, or day cannot be empty'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg, 'bazi_explanations': []}), 400
        
        # 转换为整数并校验范围
        year = int(received_year)
        month = int(received_month)
        day = int(received_day)
        if year < 1900 or year > 2024:
            error_msg = 'Year must be between 1900 and 2024'
            return jsonify({'error': error_msg, 'bazi_explanations': []}), 400
        if month < 1 or month > 12:
            error_msg = 'Month must be between 1 and 12'
            return jsonify({'error': error_msg, 'bazi_explanations': []}), 400
        if day < 1 or day > 31:
            error_msg = 'Day must be between 1 and 31'
            return jsonify({'error': error_msg, 'bazi_explanations': []}), 400

        # 验证日期有效性（处理2月、30天月份等异常）
        try:
            datetime(year, month, day)
        except ValueError as e:
            error_msg = f'Invalid date: {str(e)} (e.g., February has no 30th day)'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg, 'bazi_explanations': []}), 400

        # 处理可选的时间参数（仅校验格式，不影响测算）
        hour = None
        minute = None
        if received_hour:
            try:
                hour = int(received_hour)
                if hour < 0 or hour > 23:
                    raise ValueError("Hour out of range 0-23")
            except ValueError as e:
                error_msg = f'Invalid hour: {str(e)}'
                return jsonify({'error': error_msg, 'bazi_explanations': []}), 400
        if received_minute:
            try:
                minute = int(received_minute)
                if minute < 0 or minute > 59:
                    raise ValueError("Minute out of range 0-59")
            except ValueError as e:
                error_msg = f'Invalid minute: {str(e)}'
                return jsonify({'error': error_msg, 'bazi_explanations': []}), 400

        # --------------------------
        # 关键修改：lunar-python 最新版API调用
        # --------------------------
        # 1. 正确创建公历对象（旧版本可能支持 Solar(year, month, day)，新版本需用 fromYmd 静态方法）
        solar = Solar.fromYmd(year, month, day)
        # 2. 转换为农历对象（确保获取到有效的农历数据）
        lunar = solar.getLunar()
        if not lunar:
            raise ValueError("Failed to convert solar date to lunar date (invalid date range?)")
        
        # 日志输出农历信息（便于调试）
        lunar_year = lunar.getYear()
        lunar_month = lunar.getMonth()
        lunar_day = lunar.getDay()
        gunicorn_logger.debug(
            f"/calculate solar to lunar success: solar={year}-{month:02d}-{day:02d}, "
            f"lunar={lunar_year}-{lunar_month:02d}-{lunar_day:02d} (leap={lunar.isLeap()})"
        )

        # 3. 获取八字（三柱：年、月、日）- 最新版 getEightChar() 无变更，但需校验返回值
        ba = lunar.getEightChar()
        if not ba:
            raise ValueError("Failed to get Eight Characters (BaZi) from lunar date")
        
        # 提取天干地支（确保不为空，避免KeyError）
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
        for i, (gan, zhi) in enumerate(zip(gans, zhis)):
            if not gan or not zhi:
                raise ValueError(f"Invalid BaZi component at index {i}: gan={gan}, zhi={zhi}")
        
        # 生成八字英文标识
        bazi = [f"{heavenly_stems[gan]}{earthly_branches[zhi]}" for gan, zhi in zip(gans, zhis)]
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")

        # 计算柱解释（三个解释，与前端标签对应）
        pillar_explanations = []
        for gan, zhi in zip(gans, zhis):
            gan_element = five_elements[gan]
            zhi_element = branch_elements[zhi]
            exp = get_pillar_explanation(gan_element, zhi_element)
            pillar_explanations.append(exp)

        # 日主、五行、幸运方向计算（逻辑不变，确保元素映射正确）
        day_master = gans[2]
        element = five_elements[day_master]
        original_angle = joy_directions[element]['angle']

        # 时区调整逻辑（保持原有规则，修复浮点数计算精度）
        try:
            benchmark_offset = 8.0
            user_offset = float(received_timezone)
            diff_hours = user_offset - benchmark_offset
            adjustment = diff_hours * 15  # 每小时对应15度（360度/24小时）
            angle = round(original_angle + adjustment, 2)  # 保留2位小数，避免精度问题
            angle = angle % 360  # 确保角度在0-360范围内
            if angle < 0:
                angle += 360
        except Exception as e:
            raise ValueError(f"Timezone adjustment failed: {str(e)}")

        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems[day_master]}, element={element}, "
            f"original_angle={original_angle}, adjusted_angle={angle}, "
            f"bazi_explanations={pillar_explanations}"
        )

        # 返回结果（确保字段完整，与前端匹配）
        return jsonify({
            'lunar_date': f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
            'bazi': ' '.join(bazi),  # 三个元素的八字（年 月 日）
            'bazi_explanations': pillar_explanations,  # 三个解释（与前端Year/Month/Day标签对应）
            'angle': angle  # 调整后的幸运角度
        })

    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}", exc_info=True)  # 输出完整异常栈
        return jsonify({'error': error_msg, 'bazi_explanations': []}), 400

if __name__ == '__main__':
    # 本地运行时使用，生产环境用gunicorn
    app.run(host='0.0.0.0', port=8080, debug=False)  # 关闭debug模式，避免安全风险
