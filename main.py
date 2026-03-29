from pathlib import Path

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

try:
    from astrbot.api.star import StarTools
except ImportError:
    StarTools = None

try:
    from astrbot.core.utils.astrbot_path import get_astrbot_data_path
except ImportError:
    get_astrbot_data_path = None

try:
    # AstrBot loads plugins as packages; prefer relative import.
    from .iching import IChingBot
except ImportError:
    # Fallback for local direct execution.
    from iching import IChingBot


class IChingAstrPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bot = IChingBot(data_dir=self._resolve_data_dir())

    def _resolve_data_dir(self):
        if StarTools and hasattr(StarTools, "get_data_dir"):
            try:
                data_dir = StarTools.get_data_dir(self)
                if data_dir:
                    return str(data_dir)
            except TypeError:
                try:
                    data_dir = StarTools.get_data_dir()
                    if data_dir:
                        return str(data_dir)
                except Exception:
                    pass
            except Exception:
                pass

        if get_astrbot_data_path:
            try:
                data_dir = get_astrbot_data_path() / "plugin_data" / "iching"
                data_dir.mkdir(parents=True, exist_ok=True)
                return str(data_dir)
            except Exception:
                pass

        fallback = Path(__file__).resolve().parent / "data"
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback)

    @staticmethod
    def _resolve_user_id(event: AstrMessageEvent):
        sender_id = event.get_sender_id()
        if sender_id:
            return f"id:{sender_id}"

        unified_origin = getattr(event, "unified_msg_origin", "")
        if unified_origin:
            return f"umo:{unified_origin}"

        sender_name = event.get_sender_name()
        if sender_name:
            return f"name:{sender_name}"

        return None

    @filter.command("今日运势")
    async def today_fortune(self, event: AstrMessageEvent):
        """查看今日运势"""
        yield event.plain_result(self.bot.get_today_fortune())

    @filter.command("起卦")
    async def cast_hexagram(self, event: AstrMessageEvent, n1: int, n2: int, n3: int):
        """数字起卦：起卦 3 5 7"""
        user_id = self._resolve_user_id(event)
        if not user_id:
            yield event.plain_result("无法识别用户身份，请稍后再试。")
            return

        response = self.bot.cast_hexagram_once(user_id, [n1, n2, n3])

        yield event.plain_result(response)

    @filter.command("易经帮助")
    async def help_text(self, event: AstrMessageEvent):
        """显示插件帮助"""
        yield event.plain_result(
            "可用指令:\n"
            "1) 今日运势\n"
            "2) 起卦 <数字1> <数字2> <数字3>  (示例: 起卦 3 5 7)"
        )

    async def terminate(self):
        """插件被卸载或停用时触发。"""
        self.bot.save_state()
