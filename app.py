import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# 28 Lunar Mansions with descriptions
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

# Branch Elements mapping
branch_elements = {
    'Zi': 'Water', 'Chou': 'Earth', 'Yin': 'Wood', 'Mao': 'Wood',
    'Chen': 'Earth', 'Si': 'Fire', 'Wu': 'Fire', 'Wei': 'Earth',
    'Shen': 'Metal', 'You': 'Metal', 'Xu': 'Earth', 'Hai': 'Water'
}

# Joy Directions based on Five Elements with base angles (东八区基础角度)
joy_directions_base = {
    'Wood': 0,    # 基础角度
    'Fire': 90,
    'Earth': 180,
    'Metal': 180,
    'Water': 270
}

# 健康检查端点
@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

# 八字计算端点（仅使用年月日）
@app.route('/calculate', methods=['GET'])
def calculate():
    # 记录请求参数日志
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    received_timezone = request.args.get('timezone')
    gunicorn_logger.debug(
        f"Received GET /calculate with params: year={received_year}, month={received_month}, day={received_day}, timezone={received_timezone}"
    )

    try:
        # 参数校验
        year = int(received_year) if received_year else 0
        month = int(received_month) if received_month else 0
        day = int(received_day) if received_day else 0
        
        # 处理时区参数（仅用于装饰性计算）
        try:
            timezone = float(received_timezone) if received_timezone else 8.0  # 默认东八区
        except:
            timezone = 8.0  # 无效时区时使用默认值
        
        if not (year and month and day):
            error_msg = 'Missing year, month, or day'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # 农历转换 - 始终基于东八区计算八字
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        gunicorn_logger.debug(f"/calculate solar to lunar success: solar={year}-{month}-{day}, lunar={lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}")

        # 八字计算（仅包含年月日三柱）
        ba = lunar.getEightChar()
        gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]  # 仅年、月、日
        zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]   # 仅年、月、日
        
        # 生成八字及其属性描述
        bazi = []
        bazi_attributes = []
        for g, z in zip(gans, zhis):
            stem_eng = heavenly_stems[g]
            branch_eng = earthly_branches[z]
            bazi.append(f"{stem_eng}{branch_eng}")
            bazi_attributes.append(
                f"{stem_eng}{branch_eng}: {five_elements[g]} meets {branch_elements[branch_eng]}, a celestial blend of {five_elements[g].lower()}’s strength and {branch_elements[branch_eng].lower()}’s flow"
            )
        gunicorn_logger.debug(f"/calculate BaZi generated: {', '.join(bazi)}")

        # 日主和五行（用于计算基础幸运度数）
        day_master = gans[2]
        element = five_elements[day_master]
        base_angle = joy_directions_base[element]

        # 基于时区的装饰性角度调整（15度/时区）
        # 计算与东八区的差值，然后调整角度
        timezone_diff = timezone - 8.0  # 与东八区的时差
        angle_adjustment = timezone_diff * 15  # 每个时区15度
        adjusted_angle = (base_angle + angle_adjustment) % 360  # 确保在0-360度之间
        # 四舍五入到整数度数
        lucky_degree = round(adjusted_angle)

        # 计算28星宿 (使用农历日计算索引)
        mansion_index = (lunar.getDay() - 1) % 28
        mansion = lunar_mansions[mansion_index]
        mansion_desc = lunar_mansions_descriptions[mansion]
        
        gunicorn_logger.debug(
            f"/calculate result: day_master={heavenly_stems[day_master]}, element={element}, base_angle={base_angle}, "
            f"timezone={timezone}, adjustment={angle_adjustment}, lucky_degree={lucky_degree}, mansion={mansion}"
        )

        # 生成mindfulness文本
        mindfulness_text = f"Your lucky degree is your cosmic key! Guided by the celestial {mansion}, rotate your phone to align with {lucky_degree}° and feel the universe’s harmony guide you to inner peace..."

        # 返回结果（只包含需要的字段）
        return jsonify({
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi_attributes': bazi_attributes,
            'mansion': mansion,
            'mansion_description': mansion_desc,
            'lucky_degree': lucky_degree,
            'mindfulness': mindfulness_text
        })

    except Exception as e:
        error_msg = f'Calculation failed: {str(e)}'
        gunicorn_logger.error(f"/calculate error occurred: {error_msg}")
        return jsonify({'error': error_msg}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
