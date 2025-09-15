import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar
import datetime  # 新增：用于日期验证

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
    'Metal': 145,
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
        # 参数校验 - 增强版
        if not all([received_year, received_month, received_day]):
            error_msg = 'Missing required parameters: year, month, and day are all required'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': []
            }), 400

        # 转换并验证日期
        try:
            year = int(received_year)
            month = int(received_month)
            day = int(received_day)
            
            # 验证日期有效性
            datetime.date(year, month, day)  # 这会抛出无效日期异常
            
            # 检查年份范围
            if year < 1900 or year > 2024:
                raise ValueError("Year must be between 1900 and 2024")
                
            # 检查月份范围
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")
                
            # 检查日期范围
            if day < 1 or day > 31:
                raise ValueError("Day must be between 1 and 31")
                
        except ValueError as ve:
            error_msg = f'Invalid date: {str(ve)}'
            gunicorn_logger.debug(f"/calculate date validation error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': []
            }), 400
        
        # 处理时区参数
        try:
            timezone = float(received_timezone) if received_timezone else 8.0  # 默认东八区
        except:
            timezone = 8.0
            gunicorn_logger.debug(f"Invalid timezone, using default: {timezone}")

        # 农历转换 - 增加详细日志
        try:
            solar = Solar.fromYmd(year, month, day)
            lunar = solar.getLunar()
            gunicorn_logger.debug(f"Solar to lunar conversion successful: {year}-{month}-{day} -> {lunar.getYear()}-{lunar.getMonth()}-{lunar.getDay()}")
        except Exception as e:
            error_msg = f'Failed to convert to lunar calendar: {str(e)}'
            gunicorn_logger.error(f"/calculate lunar conversion error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': []
            }), 400

        # 八字计算 - 增加详细日志
        try:
            ba = lunar.getEightChar()
            gans = [ba.getYearGan(), ba.getMonthGan(), ba.getDayGan()]
            zhis = [ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi()]
            
            # 验证八字数据
            if not gans or not zhis or len(gans) != 3 or len(zhis) != 3:
                raise ValueError("Invalid BaZi data generated")
                
            gunicorn_logger.debug(f"BaZi generated - Gans: {gans}, Zhis: {zhis}")
        except Exception as e:
            error_msg = f'Failed to calculate BaZi: {str(e)}'
            gunicorn_logger.error(f"/calculate BaZi error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': []
            }), 400
        
        # 生成八字及其属性描述
        try:
            bazi = []
            bazi_attributes = []
            for g, z in zip(gans, zhis):
                stem_eng = heavenly_stems[g]
                branch_eng = earthly_branches[z]
                bazi.append(f"{stem_eng}{branch_eng}")
                bazi_attributes.append(
                    f"{stem_eng}{branch_eng}: {five_elements[g]} meets {branch_elements[branch_eng]}, a celestial blend of {five_elements[g].lower()}’s strength and {branch_elements[branch_eng].lower()}’s flow"
                )
            gunicorn_logger.debug(f"BaZi attributes generated: {', '.join(bazi)}")
        except Exception as e:
            error_msg = f'Failed to generate BaZi attributes: {str(e)}'
            gunicorn_logger.error(f"/calculate BaZi attributes error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': []
            }), 400

        # 计算幸运度数
        try:
            day_master = gans[2]
            element = five_elements[day_master]
            base_angle = joy_directions_base[element]

            timezone_diff = timezone - 8.0
            angle_adjustment = timezone_diff * 15
            adjusted_angle = (base_angle + angle_adjustment) % 360
            lucky_degree = round(adjusted_angle)
            gunicorn_logger.debug(f"Lucky degree calculated: {lucky_degree}°")
        except Exception as e:
            error_msg = f'Failed to calculate lucky degree: {str(e)}'
            gunicorn_logger.error(f"/calculate lucky degree error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': []
            }), 400

        # 计算28星宿
        try:
            mansion_index = (lunar.getDay() - 1) % 28
            mansion = lunar_mansions[mansion_index]
            mansion_desc = lunar_mansions_descriptions[mansion]
            gunicorn_logger.debug(f"Mansion calculated: {mansion}")
        except Exception as e:
            error_msg = f'Failed to calculate lunar mansion: {str(e)}'
            gunicorn_logger.error(f"/calculate mansion error: {error_msg}")
            return jsonify({
                'error': error_msg,
                'bazi_attributes': bazi_attributes  # 保留已生成的八字数据
            }), 400

        # 生成返回结果
        return jsonify({
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi_attributes': bazi_attributes,
            'mansion': mansion,
            'mansion_description': mansion_desc,
            'lucky_degree': lucky_degree,
            'mindfulness': f"Your lucky degree is your cosmic key! Guided by the celestial {mansion}, rotate your phone to align with {lucky_degree}° and feel the universe’s harmony guide you to inner peace..."
        })

    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        gunicorn_logger.error(f"/calculate unexpected error: {error_msg}", exc_info=True)  # 记录完整堆栈信息
        return jsonify({
            'error': error_msg,
            'bazi_attributes': []
        }), 500  # 使用500表示服务器内部错误

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # 开启debug模式便于开发调试
