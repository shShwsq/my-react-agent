import uuid
import logging
from pathlib import Path
from typing import Optional
from app.tasks.tools import BaseTool, ToolResult, tool_registry

logger = logging.getLogger(__name__)

FILES_DIR = Path("storage/agent_files")

_cjk_font_configured = False


def _configure_cjk_font():
    global _cjk_font_configured
    if _cjk_font_configured:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    candidates = ["SimHei", "Microsoft YaHei", "STSong", "WenQuanYi Micro Hei", "Noto Sans CJK SC"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in candidates:
        if font_name in available:
            plt.rcParams["font.sans-serif"] = [font_name] + plt.rcParams["font.sans-serif"]
            plt.rcParams["axes.unicode_minus"] = False
            _cjk_font_configured = True
            logger.info(f"[ChartingTools] CJK font configured: {font_name}")
            return
    logger.warning("[ChartingTools] No CJK font found, Chinese text may not render correctly")


def _save_chart(fig, room_id: str, user_id: int) -> dict:
    outputs_dir = FILES_DIR / str(user_id) / room_id / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    image_id = str(uuid.uuid4())[:8]
    filename = f"chart_{image_id}.png"
    file_path = outputs_dir / filename

    fig.savefig(str(file_path), dpi=150, bbox_inches="tight", facecolor="white")
    file_size = file_path.stat().st_size

    return {
        "filename": filename,
        "file_size": file_size,
        "relative_path": file_path.relative_to(FILES_DIR).as_posix(),
        "folder": "outputs",
    }


def _run_line_chart(
    labels: list[str],
    datasets: list[dict],
    title: str,
    x_label: str,
    y_label: str,
    room_id: str,
    user_id: int,
):
    _configure_cjk_font()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))

    for ds in datasets:
        name = ds.get("name", "")
        data = ds.get("data", [])
        color = ds.get("color")
        marker = ds.get("marker", "o")
        linestyle = ds.get("linestyle", "-")

        kwargs = {"label": name, "marker": marker, "linestyle": linestyle}
        if color:
            kwargs["color"] = color
        ax.plot(labels[: len(data)], data, **kwargs)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    ax.grid(True, alpha=0.3)

    try:
        file_info = _save_chart(fig, room_id, user_id)
        return ToolResult(success=True, output={
            "chart_type": "line_chart",
            "title": title,
            "file_created": file_info,
        })
    except Exception as e:
        return ToolResult(success=False, output=None, error=f"保存图表失败: {str(e)}")
    finally:
        plt.close(fig)


def _run_bar_chart(
    labels: list[str],
    datasets: list[dict],
    title: str,
    x_label: str,
    y_label: str,
    orientation: str,
    room_id: str,
    user_id: int,
):
    _configure_cjk_font()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 6))
    n = len(datasets)
    x = np.arange(len(labels))
    width = 0.7 / max(n, 1)

    for i, ds in enumerate(datasets):
        name = ds.get("name", "")
        data = ds.get("data", [])
        color = ds.get("color")
        offset = (i - (n - 1) / 2) * width

        kwargs = {"label": name}
        if color:
            kwargs["color"] = color

        if orientation == "horizontal":
            ax.barh(x + offset, data, width, **kwargs)
        else:
            ax.bar(x + offset, data, width, **kwargs)

    if orientation == "horizontal":
        ax.set_yticks(x)
        ax.set_yticklabels(labels)
        ax.set_xlabel(y_label)
        ax.set_ylabel(x_label)
    else:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45 if len(labels) > 6 else 0, ha="right" if len(labels) > 6 else "center")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="x" if orientation == "horizontal" else "y")

    try:
        file_info = _save_chart(fig, room_id, user_id)
        return ToolResult(success=True, output={
            "chart_type": "bar_chart",
            "title": title,
            "file_created": file_info,
        })
    except Exception as e:
        return ToolResult(success=False, output=None, error=f"保存图表失败: {str(e)}")
    finally:
        plt.close(fig)


def _run_pie_chart(
    labels: list[str],
    data: list[float],
    title: str,
    room_id: str,
    user_id: int,
):
    _configure_cjk_font()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.pie(data, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title(title)

    try:
        file_info = _save_chart(fig, room_id, user_id)
        return ToolResult(success=True, output={
            "chart_type": "pie_chart",
            "title": title,
            "file_created": file_info,
        })
    except Exception as e:
        return ToolResult(success=False, output=None, error=f"保存图表失败: {str(e)}")
    finally:
        plt.close(fig)


def _run_scatter_chart(
    x_data: list[float],
    y_data: list[float],
    title: str,
    x_label: str,
    y_label: str,
    labels: Optional[list[str]],
    room_id: str,
    user_id: int,
):
    _configure_cjk_font()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(x_data, y_data, alpha=0.7, edgecolors="k", linewidths=0.5)

    if labels:
        for i, label in enumerate(labels):
            if i < len(x_data) and i < len(y_data):
                ax.annotate(label, (x_data[i], y_data[i]), fontsize=8, alpha=0.7)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3)

    try:
        file_info = _save_chart(fig, room_id, user_id)
        return ToolResult(success=True, output={
            "chart_type": "scatter_chart",
            "title": title,
            "file_created": file_info,
        })
    except Exception as e:
        return ToolResult(success=False, output=None, error=f"保存图表失败: {str(e)}")
    finally:
        plt.close(fig)


class LineChartTool(BaseTool):
    name = "line_chart"
    description = "绘制折线图。支持多条数据线、自定义颜色和标记。适用于展示数据随时间或类别的变化趋势"

    async def execute(self, **kwargs) -> ToolResult:
        import asyncio

        labels = kwargs.get("labels", [])
        datasets = kwargs.get("datasets", [])
        title = kwargs.get("title", "折线图")
        x_label = kwargs.get("x_label", "")
        y_label = kwargs.get("y_label", "")
        room_id = kwargs.get("room_id", "default")
        user_id = kwargs.get("user_id", 0)

        if not labels or not datasets:
            return ToolResult(success=False, output=None, error="labels 和 datasets 不能为空")

        for ds in datasets:
            if "data" not in ds:
                return ToolResult(success=False, output=None, error="每个 dataset 必须包含 data 字段")

        return await asyncio.to_thread(
            _run_line_chart, labels, datasets, title, x_label, y_label, room_id, user_id
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "X 轴标签列表，如 ['1月', '2月', '3月']"
                },
                "datasets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "数据系列名称"},
                            "data": {"type": "array", "items": {"type": "number"}, "description": "数据值列表"},
                            "color": {"type": "string", "description": "线条颜色，如 'red'、'#FF5733'（可选）"},
                            "marker": {"type": "string", "description": "数据点标记样式，如 'o'、's'、'^'（可选）"},
                            "linestyle": {"type": "string", "description": "线条样式，如 '-'、'--'、'-.'（可选）"}
                        },
                        "required": ["data"]
                    },
                    "description": "数据系列列表，每个系列包含 name、data，可选 color、marker、linestyle"
                },
                "title": {"type": "string", "description": "图表标题，默认'折线图'"},
                "x_label": {"type": "string", "description": "X 轴标签（可选）"},
                "y_label": {"type": "string", "description": "Y 轴标签（可选）"}
            },
            "required": ["labels", "datasets"]
        }


class BarChartTool(BaseTool):
    name = "bar_chart"
    description = "绘制柱状图。支持多组数据对比、水平/垂直方向。适用于不同类别间的数值比较"

    async def execute(self, **kwargs) -> ToolResult:
        import asyncio

        labels = kwargs.get("labels", [])
        datasets = kwargs.get("datasets", [])
        title = kwargs.get("title", "柱状图")
        x_label = kwargs.get("x_label", "")
        y_label = kwargs.get("y_label", "")
        orientation = kwargs.get("orientation", "vertical")
        room_id = kwargs.get("room_id", "default")
        user_id = kwargs.get("user_id", 0)

        if not labels or not datasets:
            return ToolResult(success=False, output=None, error="labels 和 datasets 不能为空")

        for ds in datasets:
            if "data" not in ds:
                return ToolResult(success=False, output=None, error="每个 dataset 必须包含 data 字段")

        return await asyncio.to_thread(
            _run_bar_chart, labels, datasets, title, x_label, y_label, orientation, room_id, user_id
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "类别标签列表，如 ['产品A', '产品B', '产品C']"
                },
                "datasets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "数据系列名称"},
                            "data": {"type": "array", "items": {"type": "number"}, "description": "数据值列表"},
                            "color": {"type": "string", "description": "柱体颜色，如 'blue'、'#4CAF50'（可选）"}
                        },
                        "required": ["data"]
                    },
                    "description": "数据系列列表，每个系列包含 name、data，可选 color"
                },
                "title": {"type": "string", "description": "图表标题，默认'柱状图'"},
                "x_label": {"type": "string", "description": "X 轴标签（可选）"},
                "y_label": {"type": "string", "description": "Y 轴标签（可选）"},
                "orientation": {
                    "type": "string",
                    "enum": ["vertical", "horizontal"],
                    "description": "柱体方向，默认 vertical（垂直），可选 horizontal（水平）"
                }
            },
            "required": ["labels", "datasets"]
        }


class PieChartTool(BaseTool):
    name = "pie_chart"
    description = "绘制饼图。适用于展示各部分占总体的比例关系"

    async def execute(self, **kwargs) -> ToolResult:
        import asyncio

        labels = kwargs.get("labels", [])
        data = kwargs.get("data", [])
        title = kwargs.get("title", "饼图")
        room_id = kwargs.get("room_id", "default")
        user_id = kwargs.get("user_id", 0)

        if not labels or not data:
            return ToolResult(success=False, output=None, error="labels 和 data 不能为空")

        if len(labels) != len(data):
            return ToolResult(success=False, output=None, error="labels 和 data 长度必须一致")

        return await asyncio.to_thread(
            _run_pie_chart, labels, data, title, room_id, user_id
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "各扇区标签列表，如 ['股票', '债券', '现金']"
                },
                "data": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "各扇区数值列表，如 [60, 30, 10]"
                },
                "title": {"type": "string", "description": "图表标题，默认'饼图'"}
            },
            "required": ["labels", "data"]
        }


class ScatterChartTool(BaseTool):
    name = "scatter_chart"
    description = "绘制散点图。适用于展示两个变量之间的关系和分布"

    async def execute(self, **kwargs) -> ToolResult:
        import asyncio

        x_data = kwargs.get("x_data", [])
        y_data = kwargs.get("y_data", [])
        title = kwargs.get("title", "散点图")
        x_label = kwargs.get("x_label", "")
        y_label = kwargs.get("y_label", "")
        labels = kwargs.get("labels")
        room_id = kwargs.get("room_id", "default")
        user_id = kwargs.get("user_id", 0)

        if not x_data or not y_data:
            return ToolResult(success=False, output=None, error="x_data 和 y_data 不能为空")

        if len(x_data) != len(y_data):
            return ToolResult(success=False, output=None, error="x_data 和 y_data 长度必须一致")

        return await asyncio.to_thread(
            _run_scatter_chart, x_data, y_data, title, x_label, y_label, labels, room_id, user_id
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "x_data": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "X 轴数据列表"
                },
                "y_data": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Y 轴数据列表"
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "数据点标签列表（可选），用于标注每个数据点"
                },
                "title": {"type": "string", "description": "图表标题，默认'散点图'"},
                "x_label": {"type": "string", "description": "X 轴标签（可选）"},
                "y_label": {"type": "string", "description": "Y 轴标签（可选）"}
            },
            "required": ["x_data", "y_data"]
        }


tool_registry.register(LineChartTool())
tool_registry.register(BarChartTool())
tool_registry.register(PieChartTool())
tool_registry.register(ScatterChartTool())
