import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar
import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 28星宿配置
lunar_mansions = [
    "Horn", "Neck", "Root", "Room", "Heart", "Tail", "Basket",
    "Dipper", "Ox", "Girl", "Emptiness", "Danger", "Encampment", "Wall",
    "Legs", "Bond", "Stomach", "Pleiades", "Net", "Beak",
    "Three Stars", "Well", "Ghosts", "Willow", "Star", "Extended Net", "Wings", "Chariot"
]

lunar_mansions_descriptions = {
    "Horn": "The beacon of ambition, igniting your path to success.",
    "Neck": "The guardian of balance, harmonizing your cosmic journey.",
    "Root": "The anchor of wisdom, grounding your soul in truth.",
    "Room": "The haven of growth, opening doors to new beginnings.",
    "Heart": "The star of passion, guiding your heart to cosmic love.",
    "Tail": "The spark of transformation, leading you to renewal.",
    "Basket": "The weave of abundance, attracting prosperity and joy.",
    "Dipper": "The ladle of destiny, pouring clarity into your fate.",
    "Ox": "The pillar of strength, carrying you through challenges.",
    "Girl": "The muse of grace, inspiring beauty in your actions.",
    "Emptiness": "The void of potential, inviting infinite possibilities.",
    "Danger": "The flame of courage, empowering you to face fears.",
    "Encampment": "The fortress of stability, shielding your dreams.",
    "Wall": "The barrier of protection, safeguarding your spirit.",
    "Legs": "The stride of progress, propelling you toward goals.",
    "Bond": "The tie of connection, uniting you with cosmic allies.",
    "Stomach": "The core of resilience, fueling your inner strength.",
    "Pleiades": "The cluster of insight, illuminating hidden truths.",
    "Net": "The web of opportunity, capturing luck in your path.",
    "Beak": "The point of precision, sharpening your focus and will.",
    "Three Stars": "The triad of harmony, balancing mind, body, soul.",
    "Well": "The source of vitality, nourishing your cosmic energy.",
    "Ghosts": "The whisper of ancestors, guiding with ancient wisdom.",
    "Willow": "The branch of flexibility, bending with life’s flow.",
    "Star": "The light of destiny, shining on your true purpose.",
    "Extended Net": "The reach of ambition, expanding your cosmic horizon.",
    "Wings": "The flight of freedom, soaring to new heights.",
    "Chariot": "The vehicle of progress, driving you to victory."
}

# -------------------------- 核心：八字测算基础配置（重构版）--------------------------
# 天干（10个，循环）
heavenly_stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
# 地支（12个，循环）
earthly_branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
# 天干对应的五行
stem_element = {
    '甲': 'Wood', '乙': 'Wood', '丙': 'Fire', '丁': 'Fire', 
    '戊': 'Earth', '己': 'Earth', '庚': 'Metal', '辛': 'Metal', 
    '壬': 'Water', '癸': 'Water'
}
# 地支对应的五行
branch_element = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood',
    '辰': 'Earth', '巳': 'Fire', '午': 'Fire', '未': 'Earth',
    '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water'
}
# 天干英文映射
heavenly_stems_en = {
    '甲': 'Jia', '乙': 'Yi', '丙': 'Bing', '丁': 'Ding', 
    '戊': 'Wu', '己': 'Ji', '庚': 'Geng', '辛': 'Xin', 
    '壬': 'Ren', '癸': 'Gui'
}
# 地支英文映射
earthly_branches_en = {
    '子': 'Zi', '丑': 'Chou', '寅': 'Yin', '卯': 'Mao', 
    '辰': 'Chen', '巳': 'Si', '午': 'Wu', '未': 'Wei', 
    '申': 'Shen', '酉': 'You', '戌': 'Xu', '亥': 'Hai'
}
# 五行对应的基础角度
joy_directions_base = {
    'Wood': 0, 'Fire': 90, 'Earth': 180, 'Metal': 145, 'Water': 270
}

# -------------------------- 核心：八字计算函数（重构版）--------------------------
def calculate_bazi(year, month, day):
    """
    基于公历日期计算八字（年月日三柱）
    计算逻辑：
    1. 公历转农历（确保干支准确）
    2. 农历年 → 年柱（天干+地支）
    3. 农历月 → 月柱（根据节气调整，确保月柱正确）
    4. 农历日 → 日柱（直接获取）
    """
    try:
        # 1. 公历转农历（lunar_python确保准确性）
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        
        # 2. 年柱：农历年的天干+地支
        lunar_year = lunar.getYear()  # 农历年份（如2024）
        # 年干计算：(年份-3) % 10（甲为0，对应索引0）
        year_stem_idx = (lunar_year - 3) % 10
        year_stem = heavenly_stems[year_stem_idx]
        # 年支计算：(年份-3) % 12（子为0，对应索引0）
        year_branch_idx = (lunar_year - 3) % 12
        year_branch = earthly_branches[year_branch_idx]
        year_pillar = f"{year_stem}{year_branch}"  # 年柱（如甲午）
        
        # 3. 月柱：农历月的天干+地支（关键：月支固定，月干需计算）
        lunar_month = lunar.getMonth()  # 农历月份（1-12）
        # 月支固定对应（农历1月=寅，2月=卯...12月=丑）
        month_branch_idx = (lunar_month + 1) % 12  # 调整索引：1月→寅（索引2）
        month_branch = earthly_branches[month_branch_idx]
        # 月干计算：(年干索引 * 2 + 农历月) % 10
        year_stem_idx = heavenly_stems.index(year_stem)
        month_stem_idx = (year_stem_idx * 2 + lunar_month) % 10
        month_stem = heavenly_stems[month_stem_idx]
        month_pillar = f"{month_stem}{month_branch}"  # 月柱（如丙寅）
        
        # 4. 日柱：直接从农历获取（lunar_python已处理大小月、闰月）
        day_stem = lunar.getDayGan()
        day_branch = lunar.getDayZhi()
        day_pillar = f"{day_stem}{day_branch}"  # 日柱（如戊辰）
        
        # 返回三柱八字（年、月、日）
        return {
            'year_pillar': year_pillar,
            'month_pillar': month_pillar,
            'day_pillar': day_pillar,
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}"
        }
    except Exception as e:
        gunicorn_logger.error(f"八字计算失败: {str(e)}")
        raise Exception(f"Bazi calculation failed: {str(e)}")

# -------------------------- 接口配置 --------------------------
# 健康检查接口
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

# 八字计算接口（核心接口）
@app.route('/calculate', methods=['GET'])
def calculate_handler():
    # 1. 获取请求参数
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    received_timezone = request.args.get('timezone')
    gunicorn_logger.debug(
        f"收到请求参数: year={received_year}, month={received_month}, day={received_day}, timezone={received_timezone}"
    )

    try:
        # 2. 参数校验
        # 日期参数校验
        if not all([received_year, received_month, received_day]):
            raise ValueError("Missing required parameters: year, month, day")
        
        year = int(received_year)
        month = int(received_month)
        day = int(received_day)
        
        # 验证日期有效性（排除无效日期如2月30日）
        datetime.date(year, month, day)
        if year < 1900 or year > 2024:
            raise ValueError("Year must be between 1900 and 2024")
        
        # 时区参数处理（装饰性，默认UTC+8）
        try:
            timezone = float(received_timezone) if received_timezone else 8.0
        except:
            timezone = 8.0
            gunicorn_logger.debug(f"无效时区，使用默认值: {timezone}")

        # 3. 核心：计算八字（调用重构后的函数）
        bazi_result = calculate_bazi(year, month, day)
        lunar_date = bazi_result['lunar_date']
        pillars = [
            bazi_result['year_pillar'],
            bazi_result['month_pillar'],
            bazi_result['day_pillar']
        ]

        # 4. 生成八字属性描述（前端显示用）
        bazi_attributes = []
        for pillar in pillars:
            stem = pillar[0]  # 天干（如甲）
            branch = pillar[1]  # 地支（如午）
            stem_en = heavenly_stems_en[stem]
            branch_en = earthly_branches_en[branch]
            stem_elem = stem_element[stem]
            branch_elem = branch_element[branch]
            # 拼接描述文本
            attr_text = f"{stem_en}{branch_en}: {stem_elem} meets {branch_elem}, a celestial blend of {stem_elem.lower()}’s strength and {branch_elem.lower()}’s flow"
            bazi_attributes.append(attr_text)

        # 5. 计算28星宿（农历日对应索引）
        lunar_day = int(lunar_date.split('-')[2])
        mansion_index = (lunar_day - 1) % 28
        mansion = lunar_mansions[mansion_index]
        mansion_desc = lunar_mansions_descriptions[mansion]

        # 6. 计算幸运度数（基于日柱天干五行+时区装饰）
        day_stem = pillars[2][0]  # 日柱天干（日主）
        day_element = stem_element[day_stem]
        base_angle = joy_directions_base[day_element]
        # 时区装饰性调整（15度/时区，与东八区差值）
        timezone_diff = timezone - 8.0
        angle_adjustment = timezone_diff * 15
        lucky_degree = round((base_angle + angle_adjustment) % 360)

        # 7. 生成返回结果
        return jsonify({
            'lunar_date': lunar_date,
            'bazi_attributes': bazi_attributes,
            'mansion': mansion,
            'mansion_description': mansion_desc,
            'lucky_degree': lucky_degree,
            'mindfulness': f"Your lucky degree is your cosmic key! Guided by the celestial {mansion}, rotate your phone to align with {lucky_degree}° and feel the universe’s harmony guide you to inner peace..."
        })

    except ValueError as ve:
        # 参数错误（明确提示用户）
        error_msg = f"Invalid parameter: {str(ve)}"
        gunicorn_logger.error(error_msg)
        return jsonify({'error': error_msg, 'bazi_attributes': []}), 400
    except Exception as e:
        # 其他未知错误
        error_msg = f"Calculation failed: {str(e)}"
        gunicorn_logger.error(error_msg, exc_info=True)
        return jsonify({'error': error_msg, 'bazi_attributes': []}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
