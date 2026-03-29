"""
IChingBot - 易经算卦机器人插件
Version: 1.0.0
Description: 提供今日运势查看和梅花易数/数字起卦功能。支持北京时间每日限次。
"""

import datetime
from datetime import timedelta, timezone
import hashlib
import json
from pathlib import Path
import random
import threading

class IChingBot:
    """
    易经算卦核心类
    """
    def __init__(self, data_dir=None):
        # 记录用户当前对话状态 {user_id: 'state'}
        self.user_states = {}
        # 记录用户持久化数据 {user_id: {'last_cast_date': date_obj}}
        self.user_data = {}
        self._lock = threading.RLock()
        self._data_file = None

        if data_dir:
            data_path = Path(data_dir)
            data_path.mkdir(parents=True, exist_ok=True)
            self._data_file = data_path / "state.json"

        # 定义北京时区 (UTC+8)
        self.beijing_tz = timezone(timedelta(hours=8))
        
        # 八卦基础数据 (Ba Gua Trigrams)
        self.trigrams = {
            1: "乾 (天)",
            2: "兑 (泽)",
            3: "离 (火)",
            4: "震 (雷)",
            5: "巽 (风)",
            6: "坎 (水)",
            7: "艮 (山)",
            8: "坤 (地)"
        }
        
        # 64卦名映射表 (上卦, 下卦) -> 卦名
        # 基于文王64卦顺序，使用 (上卦数字, 下卦数字) 作为键
        self.hexagram_map = {
            (1, 1): "乾为天", (1, 2): "天泽履", (1, 3): "天火同人", (1, 4): "天雷无妄", (1, 5): "天风姤", (1, 6): "天水讼", (1, 7): "天山遯", (1, 8): "天地否",
            (2, 1): "泽天夬", (2, 2): "兑为泽", (2, 3): "泽火革", (2, 4): "泽雷随", (2, 5): "泽风大过", (2, 6): "泽水困", (2, 7): "泽山咸", (2, 8): "泽地萃",
            (3, 1): "火天大有", (3, 2): "火泽睽", (3, 3): "离为火", (3, 4): "火雷噬嗑", (3, 5): "火风鼎", (3, 6): "火水未济", (3, 7): "火山旅", (3, 8): "火地晋",
            (4, 1): "雷天大壮", (4, 2): "雷泽归妹", (4, 3): "雷火丰", (4, 4): "震为雷", (4, 5): "雷风恒", (4, 6): "雷水解", (4, 7): "雷山小过", (4, 8): "雷地豫",
            (5, 1): "风天小畜", (5, 2): "风泽中孚", (5, 3): "风火家人", (5, 4): "风雷益", (5, 5): "巽为风", (5, 6): "风水涣", (5, 7): "风山渐", (5, 8): "风地观",
            (6, 1): "水天需", (6, 2): "水泽节", (6, 3): "水火既济", (6, 4): "水雷屯", (6, 5): "水风井", (6, 6): "坎为水", (6, 7): "水山蹇", (6, 8): "水地比",
            (7, 1): "山天大畜", (7, 2): "山泽损", (7, 3): "山火贲", (7, 4): "山雷颐", (7, 5): "山风蛊", (7, 6): "山水蒙", (7, 7): "艮为山", (7, 8): "山地剥",
            (8, 1): "地天泰", (8, 2): "地泽临", (8, 3): "地火明夷", (8, 4): "地雷复", (8, 5): "地风升", (8, 6): "地水师", (8, 7): "地山谦", (8, 8): "坤为地",
        }

        # 64卦简要卦辞与吉凶
        self.hexagram_meanings = {
            "乾为天": "【大吉】天行健，君子以自强不息。象征天，刚健之意。",
            "坤为地": "【大吉】地势坤，君子以厚德载物。象征地，柔顺之意。",
            "水雷屯": "【下下】万物始生，艰难险阻。需耐心等待时机。",
            "山水蒙": "【中下】童蒙初开，启迪智慧。需良师益友指引。",  
            "水天需": "【中上】守正待机，饮食宴乐。耐心等待会有好结果。",
            "天水讼": "【下下】争端纷争，慎始敬终。避免口舌是非。",
            "地水师": "【中上】行军征战，统帅之才。需严明纪律。",
            "水地比": "【上上】亲近依附，和乐相处。贵人相助。",
            "风天小畜": "【下下】积蓄力量，时机未到。不可急于求成。",
            "天泽履": "【中上】小心谨慎，如履薄冰。循规蹈矩可保平安。",
            "地天泰": "【上上】阴阳交泰，万物通达。诸事顺利。",
            "天地否": "【下下】阴阳不交，闭塞不通。需防小人。",
            "天火同人": "【上上】上下和同，团结一心。利于合作。",
            "火天大有": "【上上】盛大富有，顺天应人。事业大成。",
            "地山谦": "【上上】谦虚受益，满招损。以退为进。",
            "雷地豫": "【中上】顺时依势，安乐欢愉。利于出行。",
            "泽雷随": "【中上】随机应变，顺从悦服。顺势而为。",
            "山风蛊": "【中下】振疲起衰，整顿改革。需革除旧弊。",
            "地泽临": "【上上】亲临督导，时运亨通。把握良机。",
            "风地观": "【中上】观察瞻仰，神道设教。静观其变。",
            "火雷噬嗑": "【中下】严明刑罚，去除障碍。需果断行动。",
            "山火贲": "【中上】装饰文饰，光彩照人。外表华丽，需重内涵。",
            "山地剥": "【下下】剥落侵蚀，顺势而止。宜守不宜进。",
            "地雷复": "【中上】剥极而复，万物更新。否极泰来。",
            "天雷无妄": "【中上】顺守正道，无妄之灾。切勿心存侥幸。",
            "山天大畜": "【上上】积蓄德行，大有所为。时机成熟。",
            "山雷颐": "【中上】颐养身心，言语谨慎。祸从口出。",
            "泽风大过": "【下下】非常之时，行非常之事。压力巨大，需谨慎。",
            "坎为水": "【下下】重重险阻，习坎修德。守正待时。",
            "离为火": "【中上】依附光明，继明照四方。需依附正道。",
            "泽山咸": "【上上】感应沟通，夫妇之道。感情和睦。",
            "雷风恒": "【上上】持之以恒，立不易方。坚持到底。",
            "天山遯": "【下下】隐退避让，适时而止。急流勇退。",
            "雷天大壮": "【中上】壮大强盛，非礼勿履。切勿莽撞。",
            "火地晋": "【上上】进长盛进，日出地上。步步高升。",
            "地火明夷": "【下下】韬光养晦，艰苦守贞。需忍耐。",
            "风火家人": "【上上】正家而治，相夫教子。家庭和睦。",
            "火泽睽": "【下下】人心乖离，求大同存小异。诸事不顺。",
            "水山蹇": "【下下】艰难险阻，反身修德。寸步难行。",
            "雷水解": "【中上】缓解险难，赦过宥罪。问题解决。",
            "山泽损": "【中下】损下益上，惩忿窒欲。先失后得。",
            "风雷益": "【上上】损上益下，见善则迁。利于进取。",
            "泽天夬": "【中上】决断清除，刚决柔。需果断决策。",
            "天风姤": "【中下】风云相遇，不期而遇。防范烂桃花。",
            "泽地萃": "【上上】聚集融合，居安思危。群英荟萃。",
            "地风升": "【上上】积小成大，顺势上升。步步高升。",
            "泽水困": "【下下】困境磨练，致命遂志。陷入困境。",
            "水风井": "【中上】开发资源，养民无穷。修身养性。",
            "泽火革": "【中上】变革创新，顺天应人。改旧换新。",
            "火风鼎": "【中上】稳重图变，去故取新。三足鼎立。",
            "震为雷": "【中下】临危不惧，修省反思。需小心谨慎。",
            "艮为山": "【中下】动静适时，止其所止。宜静不宜动。",
            "风山渐": "【上上】循序渐进，积少成多。好事多磨。",
            "雷泽归妹": "【下下】少女出嫁，未必如愿。错失良机。",
            "雷火丰": "【上上】盛大丰满，日中则昃。如日中天。",
            "火山旅": "【中下】羁旅漂泊，守正安邦。奔波劳碌。",
            "巽为风": "【中上】谦逊顺从，申命行事。顺势而为。",
            "兑为泽": "【上上】喜悦沟通，朋友讲习。心情愉悦。",
            "风水涣": "【下下】消除隔阂，拯救涣散。需凝聚人心。",
            "水泽节": "【中上】节制调控，苦节不可贞。适可而止。",
            "风泽中孚": "【上上】诚信立身，心心相印。诚实守信。",
            "雷山小过": "【中下】小事可做，大事不可。需谨慎行事。",
            "水火既济": "【上上】事情完成，初吉终乱。功德圆满。",
            "火水未济": "【下下】事情未完，重新开始。前途未卜。"
        }

        # 每日宜忌活动池
        self.lucky_activities = ["出行", "交易", "动土", "祈福", "嫁娶", "移徙", "开市", "安床", "入宅", "纳财", "祭祀", "修造", "上梁", "栽种"]
        self.unlucky_activities = ["安葬", "探病", "词讼", "行丧", "破土", "掘井", "开仓", "伐木", "作灶", "针灸"]

        self._load_state()

    @staticmethod
    def _date_to_str(date_obj):
        return date_obj.isoformat()

    @staticmethod
    def _str_to_date(date_str):
        try:
            return datetime.date.fromisoformat(date_str)
        except (TypeError, ValueError):
            return None

    def _today_bj(self):
        return datetime.datetime.now(self.beijing_tz).date()

    def _load_state(self):
        if not self._data_file or not self._data_file.exists():
            return

        try:
            raw = json.loads(self._data_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        user_states = raw.get("user_states")
        if isinstance(user_states, dict):
            self.user_states = {
                str(k): str(v) for k, v in user_states.items() if isinstance(v, str)
            }

        raw_user_data = raw.get("user_data")
        if isinstance(raw_user_data, dict):
            parsed_user_data = {}
            for user_id, info in raw_user_data.items():
                if not isinstance(info, dict):
                    continue
                last_date = self._str_to_date(info.get("last_cast_date"))
                if last_date is None:
                    continue
                parsed_user_data[str(user_id)] = {"last_cast_date": last_date}
            self.user_data = parsed_user_data

    def _save_state_locked(self):
        if not self._data_file:
            return

        serializable_user_data = {}
        for user_id, info in self.user_data.items():
            if not isinstance(info, dict):
                continue
            last_date = info.get("last_cast_date")
            if isinstance(last_date, datetime.date):
                serializable_user_data[user_id] = {
                    "last_cast_date": self._date_to_str(last_date)
                }

        payload = {
            "user_states": self.user_states,
            "user_data": serializable_user_data,
        }

        tmp_file = self._data_file.with_suffix(".tmp")
        try:
            tmp_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_file.replace(self._data_file)
        except OSError:
            return

    def save_state(self):
        with self._lock:
            self._save_state_locked()

    def can_cast_today(self, user_id):
        with self._lock:
            today_bj = self._today_bj()
            user_info = self.user_data.get(user_id, {})
            return user_info.get("last_cast_date") != today_bj

    def cast_hexagram_once(self, user_id, nums):
        with self._lock:
            today_bj = self._today_bj()
            user_info = self.user_data.get(user_id, {})
            last_date = user_info.get("last_cast_date")
            if last_date == today_bj:
                return "🚫 今日已起过卦。每日00:00刷新，卦不敢算尽，畏天道无常，请明日再来。"

            response = self.calculate_hexagram(nums)
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            self.user_data[user_id]["last_cast_date"] = today_bj
            self.user_states[user_id] = "idle"
            self._save_state_locked()
            return response

    def get_ganzhi_date(self, date):
        """
        计算简单的日干支（以2024-03-01甲子日为基准）
        """
        base_date = datetime.date(2024, 3, 1)
        days_passed = (date - base_date).days
        
        tian_gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        di_zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        # Calculate index (0 = 甲子)
        idx = days_passed % 60
        
        gan = tian_gan[idx % 10]
        zhi = di_zhi[idx % 12]
        
        return f"{gan}{zhi}" 

    def get_today_fortune(self):
        """
        生成今日运势
        """
        # 使用北京时间
        today = datetime.datetime.now(self.beijing_tz).date()
        date_str = today.strftime("%Y%m%d")
        
        # 伪随机但基于日期确定，保证所有人同一天看到的一样
        seed = int(hashlib.sha256(date_str.encode('utf-8')).hexdigest(), 16)
        r = random.Random(seed)
        
        todays_yi = r.sample(self.lucky_activities, 3)
        todays_ji = r.sample(self.unlucky_activities, 3)
        
        ganzhi = self.get_ganzhi_date(today)
        
        return f"📅 公历日期: {today}\n🗓️ 简算干支: {ganzhi}日\n\n✅ 宜: {' '.join(todays_yi)}\n❌ 忌: {' '.join(todays_ji)}"

    def calculate_hexagram(self, nums):
        """
        根据三个数字起卦 (梅花易数简易变种)
        """
        if not isinstance(nums, (list, tuple)):
            raise ValueError("请输入三个整数。")
        if len(nums) != 3:
            raise ValueError("请提供三个数字，中间用空格分开。")

        try:
            n1, n2, n3 = (int(nums[0]), int(nums[1]), int(nums[2]))
        except (TypeError, ValueError):
            raise ValueError("输入格式有误，请输入三个整数。") from None
        
        # 上卦: n1 % 8
        upper = n1 % 8
        if upper == 0: upper = 8
        
        # 下卦: n2 % 8
        lower = n2 % 8
        if lower == 0: lower = 8
        
        # 变爻: n3 % 6
        cycle = n3 % 6
        if cycle == 0: cycle = 6
        
        original_hex = self.hexagram_map.get((upper, lower), "未知卦")
        hex_meaning = self.hexagram_meanings.get(original_hex, "暂无详解")
        upper_name = self.trigrams[upper]
        lower_name = self.trigrams[lower]
        
        return (f"🔮 算卦结果:\n"
                f"上卦: {upper_name}\n"
                f"下卦: {lower_name}\n"
                f"变爻: 第{cycle}爻\n"
                f"📜 本卦: 【{original_hex}】\n"
                f"💡 卦辞概览: {hex_meaning}")

    def chat(self, user_id, message):
        """
        核心交互方法
        :param user_id: 用户唯一标识
        :param message: 用户发送的消息文本
        :return: 机器人的回复文本
        """
        if not isinstance(user_id, str) or not user_id:
            return "无法识别用户身份，请稍后再试。"
        if not isinstance(message, str):
            return "输入格式有误，请输入文本消息。"

        with self._lock:
            state = self.user_states.get(user_id, "idle")
            today_bj = self._today_bj()

            if message == "今日运势":
                return self.get_today_fortune()

            if message == "起卦":
                user_info = self.user_data.get(user_id, {})
                last_date = user_info.get("last_cast_date")
                if last_date == today_bj:
                    return "🚫 今日已起过卦。每日00:00刷新，卦不敢算尽，畏天道无常，请明日再来。"

                self.user_states[user_id] = "awaiting_numbers"
                self._save_state_locked()
                return "请给我三个数字（例如：3 5 7），我会根据这三个数字为你起卦。"

            if state == "awaiting_numbers":
                try:
                    # 兼容中文逗号和空格
                    clean_msg = message.replace(",", " ").replace("，", " ")
                    parts = clean_msg.split()
                    response = self.calculate_hexagram(parts)

                    if user_id not in self.user_data:
                        self.user_data[user_id] = {}
                    self.user_data[user_id]["last_cast_date"] = today_bj
                    self.user_states[user_id] = "idle"
                    self._save_state_locked()
                    return response
                except ValueError as exc:
                    return str(exc)

            return "我是算卦插件。请输入【今日运势】查看运势，或输入【起卦】进行排盘。"
