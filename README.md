# IChingBot 易经算卦插件

这是一个基于Python的纯文本交互式算卦插件，适用于集成到任何聊天机器人框架中。

## 功能特性

1.  **今日运势 (Daily Fortune)**
    *   根据日期计算干支。
    *   每日宜忌推算（基于日期哈希，同日结果固定）。
    *   支持北京时间 (UTC+8)。

2.  **梅花易数起卦 (Hexagram Casting)**
    *   用户输入三个数字进行起卦。
    *   返回：上卦、下卦、变爻。
    *   附带：本卦卦名及吉凶详解。
    *   **每日限次**：每个用户每日（北京时间 00:00 刷新）仅限成功起卦一次。

## 文件结构

*   `iching.py`: 核心代码文件，包含 `IChingBot` 类。
*   `requirements.txt`: 依赖说明（无第三方依赖）。

## 部署与集成

### 1. 环境要求
*   Python 3.6+
*   无需安装额外的 pip 包。

### 2. 调用示例

在你的主程序或服务器代码中：

```python
from iching import IChingBot

# 初始化
bot = IChingBot()

# 当收到用户消息时调用 chat 方法
# user_id: 用户的唯一标识符 (str)
# message: 用户发送的文本内容 (str)
response = bot.chat(user_id="user_123", message="今日运势")
print(response)

# 起卦流程示例
# 1. 用户发送 "起卦"
reply1 = bot.chat("user_123", "起卦") 
# reply1 -> "请给我三个数字..."

# 2. 用户发送数字 "3 5 7"
reply2 = bot.chat("user_123", "3 5 7")
# reply2 -> "🔮 算卦结果: ..."
```

## 注意事项

*   **数据持久化**：当前的 `user_states` 和 `user_data` 存储在内存字典中。如果服务器重启，用户的“每日已算”状态会重置。如果需要持久化，建议修改 `__init__` 与数据读写逻辑对接数据库（如 Redis 或 SQL）。
*   **时区**：代码内置 `datetime.timezone(datetime.timedelta(hours=8))` 以强制使用北京时间，不受服务器本地时区影响。

## 修改配置

*   若要修改每日宜忌的词库，请编辑 `iching.py` 中的 `self.lucky_activities` 和 `self.unlucky_activities` 列表。
