from datetime import datetime

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

try:
    # AstrBot loads plugins as packages; prefer relative import.
    from .iching import IChingBot
except ImportError:
    # Fallback for local direct execution.
    from iching import IChingBot


class IChingAstrPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bot = IChingBot()

    @filter.command("今日运势")
    async def today_fortune(self, event: AstrMessageEvent):
        """查看今日运势"""
        yield event.plain_result(self.bot.get_today_fortune())

    @filter.command("起卦")
    async def cast_hexagram(self, event: AstrMessageEvent, n1: int, n2: int, n3: int):
        """数字起卦：起卦 3 5 7"""
        user_id = event.get_sender_id() or event.get_sender_name() or "unknown_user"
        today_bj = datetime.now(self.bot.beijing_tz).date()
        user_info = self.bot.user_data.get(user_id, {})
        last_date = user_info.get("last_cast_date")

        if last_date == today_bj:
            yield event.plain_result(
                "🚫 今日已起过卦。每日00:00刷新，卦不敢算尽，畏天道无常，请明日再来。"
            )
            return

        response = self.bot.calculate_hexagram([n1, n2, n3])
        if user_id not in self.bot.user_data:
            self.bot.user_data[user_id] = {}
        self.bot.user_data[user_id]["last_cast_date"] = today_bj

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
