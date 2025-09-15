import logging
logging.basicConfig(level=logging.DEBUG)
gunicorn_logger = logging.getLogger('gunicorn')
gunicorn_logger.setLevel(logging.DEBUG)

from flask import Flask, jsonify, request
from flask_cors import CORS
from lunar_python import Solar, Lunar
import datetime

app = Flask(__name__)
CORS(app, origins=["https://www.yourluckycompass.com", "http://localhost:8080"])

# 28星宿及其描述（从当前版本引入）
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
    "Willow": "The branch of flexibility, bending with life's flow.",
    "Star": "The light of destiny, shining on your true purpose.",
    "Extended Net": "The reach of ambition, expanding your cosmic horizon.",
    "Wings": "The flight of freedom, soaring to new heights.",
    "Chariot": "The vehicle of progress, driving you to victory."
}

# 天干英文映射
heavenly_stems = {
    '甲': 'Jia', '乙': 'Yi', '丙': 'Bing', '丁': 'Ding', 
    '戊': 'Wu', '己': 'Ji', '庚': 'Geng', '辛': 'Xin', 
    '壬': 'Ren', '癸': 'Gui'
}

# 地支英文映射
earthly_branches = {
    '子': 'Zi', '丑': 'Chou', '寅': 'Yin', '卯': 'Mao', 
    '辰': 'Chen', '巳': 'Si', '午': 'Wu', '未': 'Wei', 
    '申': 'Shen', '酉': 'You', '戌': 'Xu', '亥': 'Hai'
}

# 五行映射
five_elements = {
    '甲': 'Wood', '乙': 'Wood', '丙': 'Fire', '丁': 'Fire', 
    '戊': 'Earth', '己': 'Earth', '庚': 'Metal', '辛': 'Metal', 
    '壬': 'Water', '癸': 'Water'
}

# 地支五行映射（从当前版本引入）
branch_elements = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood',
    '辰': 'Earth', '巳': 'Fire', '午': 'Fire', '未': 'Earth',
    '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water'
}

# 五行幸运方向基础角度（东八区，从当前版本引入）
joy_directions_base = {
    'Wood': 0,
    'Fire': 90,
    'Earth': 180,
    'Metal': 145,
    'Water': 270
}

@app.route('/health', methods=['GET'])
def health():
    gunicorn_logger.debug('Health check accessed')
    return jsonify({'status': 'ok'}), 200

@app.route('/calculate', methods=['GET'])
def calculate():
    received_year = request.args.get('year')
    received_month = request.args.get('month')
    received_day = request.args.get('day')
    received_timezone = request.args.get('timezone')
    
    gunicorn_logger.debug(
        f"Received GET /calculate with params: year={received_year}, month={received_month}, day={received_day}, timezone={received_timezone}"
    )

    try:
        # 参数校验
        if not all([received_year, received_month, received_day]):
            error_msg = 'Missing required parameters: year, month, and day are all required'
            gunicorn_logger.debug(f"/calculate parameter error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        try:
            year = int(received_year)
            month = int(received_month)
            day = int(received_day)
            
            # 验证日期有效性
            datetime.date(year, month, day)
            if year < 1900 or year > 2100:
                raise ValueError("Year must be between 1900 and 2100")
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")
            if day < 1 or day > 31:
                raise ValueError("Day must be between 1 and 31")
            gunicorn_logger.debug(f"Date validated: {year}-{month}-{day}")
        except ValueError as ve:
            error_msg = f'Invalid date: {str(ve)}'
            gunicorn_logger.debug(f"/calculate date validation error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # 处理时区参数
        try:
            timezone = float(received_timezone) if received_timezone else 8.0
            gunicorn_logger.debug(f"Timezone: {timezone}")
        except ValueError:
            timezone = 8.0
            gunicorn_logger.debug(f"Invalid timezone, using default: {timezone}")

        # 农历转换
        try:
            solar = Solar.fromYmd(year, month, day)
            lunar = solar.getLunar()
            gunicorn_logger.debug(f"Solar to lunar conversion successful: {year}-{month}-{day} -> {lunar.getYear()}-{lunar.getMonth()}-{lunar.getDay()}")
        except Exception as e:
            error_msg = f'Failed to convert to lunar calendar: {str(e)}'
            gunicorn_logger.error(f"/calculate lunar conversion error: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 400

        # 八字计算
        try:
            eight_char = lunar.getEightChar()
            year_gan = eight_char.getYearGan()
            year_zhi = eight_char.getYearZhi()
            month_gan = eight_char.getMonthGan()
            month_zhi = eight_char.getMonthZhi()
            day_gan = eight_char.getDayGan()
            day_zhi = eight_char.getDayZhi()
            gans = [year_gan, month_gan, day_gan]
            zhis = [year_zhi, month_zhi, day_zhi]
            gunicorn_logger.debug(f"BaZi generated - Gans: {gans}, Zhis: {zhis}")
        except Exception as e:
            error_msg = f'Failed to calculate BaZi: {str(e)}'
            gunicorn_logger.error(f"/calculate BaZi error: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 400

        # 生成八字属性（适配前端）
        try:
            bazi_attributes = []
            for i, (g, z) in enumerate(zip(gans, zhis)):
                stem_eng = heavenly_stems.get(g, g)
                branch_eng = earthly_branches.get(z, z)
                element_g = five_elements.get(g, "Unknown")
                element_z = branch_elements.get(z, "Unknown")
                position = ["Year", "Month", "Day"][i]
                bazi_attributes.append(
                    f"{position}: {stem_eng}{branch_eng} ({element_g} meets {element_z})"
                )
            gunicorn_logger.debug(f"BaZi attributes: {bazi_attributes}")
        except Exception as e:
            error_msg = f'Failed to generate BaZi attributes: {str(e)}'
            gunicorn_logger.error(f"/calculate BaZi attributes error: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 400

        # 计算幸运度数
        try:
            day_master = gans[2]
            element = five_elements.get(day_master, 'Earth')
            base_angle = joy_directions_base.get(element, 180)
            timezone_diff = timezone - 8.0
            angle_adjustment = timezone_diff * 15
            adjusted_angle = (base_angle + angle_adjustment) % 360
            lucky_degree = round(adjusted_angle)
            gunicorn_logger.debug(f"Lucky degree calculated: {lucky_degree}° (day_master={day_master}, element={element})")
        except Exception as e:
            error_msg = f'Failed to calculate lucky degree: {str(e)}'
            gunicorn_logger.error(f"/calculate lucky degree error: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 400

        # 计算28星宿
        try:
            lunar_day = lunar.getDay()
            mansion_index = (lunar_day - 1) % 28
            mansion = lunar_mansions[mansion_index]
            mansion_desc = lunar_mansions_descriptions.get(mansion, "A celestial guide in your cosmic journey.")
            gunicorn_logger.debug(f"Mansion calculated: {mansion} (day {lunar_day}, index {mansion_index})")
        except Exception as e:
            error_msg = f'Failed to calculate lunar mansion: {str(e)}'
            gunicorn_logger.error(f"/calculate mansion error: {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 400

        # 返回结果（适配前端期望的字段）
        result = {
            'lunar_date': f"{lunar.getYear()}-{lunar.getMonth():02d}-{lunar.getDay():02d}",
            'bazi_attributes': bazi_attributes,
            'mansion': mansion,
            'mansion_description': mansion_desc,
            'lucky_degree': lucky_degree
        }
        gunicorn_logger.debug(f"Response: {result}")
        return jsonify(result)

    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        gunicorn_logger.error(f"/calculate unexpected error: {error_msg}", exc_info=True)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
