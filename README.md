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

### 2. CLI/代码调用示例
（见上文）

### 3. Web 网页版部署

1.  安装依赖：
    ```bash
    pip install Flask
    ```

2.  启动 Web 服务器：
    ```bash
    python app.py
    ```

3.  浏览器访问：
    *   打开 `http://localhost:5000` 即可看到网页版聊天界面。
    *   支持多用户会话隔离（基于浏览器 Cookie/Session）。

## 注意事项

*   **数据持久化**：当前的 `user_states` 和 `user_data` 存储在内存字典中。服务器重启后数据会丢失。
*   **Web 安全**：`app.py` 中的 `secret_key` 目前是生成的随机值，每次重启服务器会导致旧 Session 失效。生产环境建议设置固定的环境变量。
*   **时区**：代码内置 `datetime.timezone(datetime.timedelta(hours=8))` 以强制使用北京时间，不受服务器本地时区影响。

## 修改配置

*   若要修改每日宜忌的词库，请编辑 `iching.py` 中的 `self.lucky_activities` 和 `self.unlucky_activities` 列表。
