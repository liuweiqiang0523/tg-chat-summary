"""图片生成模块"""

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .summarizer import SummaryResult


class ImageGenerator:
    """总结图片生成器"""

    # 颜色方案
    THEMES = {
        "dark": {
            "bg": "#1a1a2e",
            "card": "#16213e",
            "text": "#ffffff",
            "accent": "#0f3460",
            "highlight": "#e94560",
            "muted": "#8892b0",
        },
        "light": {
            "bg": "#f5f5f5",
            "card": "#ffffff",
            "text": "#333333",
            "accent": "#4a90d9",
            "highlight": "#e74c3c",
            "muted": "#666666",
        },
    }

    def __init__(self, theme: str = "dark", width: int = 800):
        self.theme = self.THEMES.get(theme, self.THEMES["dark"])
        self.width = width
        self.padding = 30
        self.card_padding = 20

    async def generate(
        self,
        result: SummaryResult,
        language: str = "zh",
        title: str = None
    ) -> BytesIO:
        """生成总结图片"""
        # 计算高度（动态）
        height = self._calculate_height(result, language)

        # 创建图片
        img = Image.new("RGB", (self.width, height), self.theme["bg"])
        draw = ImageDraw.Draw(img)

        # 绘制内容
        y = self.padding

        # 标题
        if title:
            y = self._draw_title(draw, title, y)
        else:
            y = self._draw_header(draw, result, y, language)

        # 统计卡片
        y = self._draw_stats_card(draw, result, y, language)

        # 话题
        if result.topics:
            y = self._draw_topics_card(draw, result, y, language)

        # 活跃用户
        if result.active_users:
            y = self._draw_users_card(draw, result, y, language)

        # 总结
        y = self._draw_summary_card(draw, result, y, language)

        # 亮点
        if result.highlights:
            y = self._draw_highlights_card(draw, result, y, language)

        # 转为 BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    def _calculate_height(self, result: SummaryResult, language: str) -> int:
        """计算图片高度"""
        height = self.padding * 2
        height += 60  # 标题
        height += 120  # 统计卡片
        height += 40 + len(result.topics[:5]) * 35  # 话题
        height += 40 + len(result.active_users[:5]) * 35  # 用户
        height += 40 + self._estimate_text_height(result.summary, self.width - 80)  # 总结
        height += 40 + len(result.highlights) * 30  # 亮点
        return height

    def _estimate_text_height(self, text: str, max_width: int) -> int:
        """估算文字高度"""
        chars_per_line = max_width // 14  # 粗略估算
        lines = len(text) // chars_per_line + text.count("\n") + 1
        return lines * 25

    def _draw_title(self, draw: ImageDraw.Draw, title: str, y: int) -> int:
        """绘制标题"""
        draw.text(
            (self.padding, y),
            f"📊 {title}",
            fill=self.theme["highlight"],
            font=self._get_font(size=28, bold=True)
        )
        return y + 50

    def _draw_header(
        self,
        draw: ImageDraw.Draw,
        result: SummaryResult,
        y: int,
        language: str
    ) -> int:
        """绘制头部"""
        start, end = result.time_range
        time_str = f"{start.strftime('%m-%d %H:%M')} - {end.strftime('%H:%M')}"

        title = "群聊总结" if language == "zh" else "Chat Summary"
        draw.text(
            (self.padding, y),
            f"📊 {title}",
            fill=self.theme["highlight"],
            font=self._get_font(size=28, bold=True)
        )
        draw.text(
            (self.padding, y + 35),
            time_str,
            fill=self.theme["muted"],
            font=self._get_font(size=16)
        )
        return y + 60

    def _draw_stats_card(
        self,
        draw: ImageDraw.Draw,
        result: SummaryResult,
        y: int,
        language: str
    ) -> int:
        """绘制统计卡片"""
        card_y = y + 10
        card_height = 100

        # 绘制卡片背景
        draw.rounded_rectangle(
            [self.padding, card_y, self.width - self.padding, card_y + card_height],
            radius=10,
            fill=self.theme["card"]
        )

        # 统计数据
        stats = [
            ("📝", str(result.total_messages), "消息" if language == "zh" else "Messages"),
            ("👥", str(result.total_users), "参与" if language == "zh" else "Users"),
            ("🎭", result.sentiment, "氛围" if language == "zh" else "Vibe"),
        ]

        x_step = (self.width - self.padding * 2) // 3
        for i, (icon, value, label) in enumerate(stats):
            x = self.padding + x_step * i + x_step // 2
            draw.text(
                (x - 20, card_y + 20),
                icon,
                fill=self.theme["text"],
                font=self._get_font(size=24)
            )
            draw.text(
                (x - 20, card_y + 50),
                value,
                fill=self.theme["highlight"],
                font=self._get_font(size=20, bold=True)
            )
            draw.text(
                (x - 20, card_y + 75),
                label,
                fill=self.theme["muted"],
                font=self._get_font(size=12)
            )

        return card_y + card_height + 10

    def _draw_topics_card(
        self,
        draw: ImageDraw.Draw,
        result: SummaryResult,
        y: int,
        language: str
    ) -> int:
        """绘制话题卡片"""
        title = "🔥 热门话题" if language == "zh" else "🔥 Hot Topics"
        return self._draw_list_card(
            draw, title,
            [f"{t['title']}" for t in result.topics[:5]],
            y
        )

    def _draw_users_card(
        self,
        draw: ImageDraw.Draw,
        result: SummaryResult,
        y: int,
        language: str
    ) -> int:
        """绘制活跃用户卡片"""
        title = "👥 活跃用户" if language == "zh" else "👥 Active Users"
        users = [f"@{u['username']} ({u['count']})" for u in result.active_users[:5]]
        return self._draw_list_card(draw, title, users, y)

    def _draw_summary_card(
        self,
        draw: ImageDraw.Draw,
        result: SummaryResult,
        y: int,
        language: str
    ) -> int:
        """绘制总结卡片"""
        title = "💡 总结" if language == "zh" else "💡 Summary"

        # 估算高度
        text_height = self._estimate_text_height(result.summary, self.width - 80)
        card_height = text_height + 60

        card_y = y + 10
        draw.rounded_rectangle(
            [self.padding, card_y, self.width - self.padding, card_y + card_height],
            radius=10,
            fill=self.theme["card"]
        )

        draw.text(
            (self.padding + 15, card_y + 15),
            title,
            fill=self.theme["highlight"],
            font=self._get_font(size=18, bold=True)
        )

        # 文字自动换行
        self._draw_wrapped_text(
            draw,
            result.summary,
            self.padding + 15,
            card_y + 45,
            self.width - self.padding * 2 - 30
        )

        return card_y + card_height + 10

    def _draw_highlights_card(
        self,
        draw: ImageDraw.Draw,
        result: SummaryResult,
        y: int,
        language: str
    ) -> int:
        """绘制亮点卡片"""
        title = "✨ 亮点" if language == "zh" else "✨ Highlights"
        highlights = [f"• {h}" for h in result.highlights[:5]]
        return self._draw_list_card(draw, title, highlights, y)

    def _draw_list_card(
        self,
        draw: ImageDraw.Draw,
        title: str,
        items: list[str],
        y: int
    ) -> int:
        """绘制列表卡片"""
        card_height = 50 + len(items) * 30
        card_y = y + 10

        draw.rounded_rectangle(
            [self.padding, card_y, self.width - self.padding, card_y + card_height],
            radius=10,
            fill=self.theme["card"]
        )

        draw.text(
            (self.padding + 15, card_y + 15),
            title,
            fill=self.theme["highlight"],
            font=self._get_font(size=18, bold=True)
        )

        for i, item in enumerate(items):
            draw.text(
                (self.padding + 25, card_y + 45 + i * 30),
                item,
                fill=self.theme["text"],
                font=self._get_font(size=14)
            )

        return card_y + card_height + 10

    def _draw_wrapped_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        x: int,
        y: int,
        max_width: int
    ):
        """绘制自动换行的文字"""
        lines = text.split("\n")
        current_y = y

        for line in lines:
            if not line:
                current_y += 20
                continue

            # 简单换行
            chars_per_line = max_width // 14
            while len(line) > chars_per_line:
                draw.text(
                    (x, current_y),
                    line[:chars_per_line],
                    fill=self.theme["text"],
                    font=self._get_font(size=14)
                )
                line = line[chars_per_line:]
                current_y += 22

            draw.text(
                (x, current_y),
                line,
                fill=self.theme["text"],
                font=self._get_font(size=14)
            )
            current_y += 22

    def _get_font(self, size: int = 16, bold: bool = False):
        """获取字体"""
        try:
            # 尝试加载系统字体
            font_name = "Arial Bold.ttf" if bold else "Arial.ttf"
            return ImageFont.truetype(font_name, size)
        except OSError:
            try:
                # 尝试其他字体
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
            except OSError:
                # 使用默认字体
                return ImageFont.load_default()
