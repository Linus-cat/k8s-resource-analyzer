import re
from pathlib import Path
from typing import List, Tuple, Optional

from app.models import NamespaceUsage


class ReportParser:
    BYTES_TO_GB = 1024 * 1024 * 1024

    FILENAME_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

    # ---- 日报文件内容前置校验规则（增量，不影响原有解析逻辑）----

    # 校验项 1：孤立单个汉字作为一个完整字段（地名被错误断字）。
    # 判定依据：正常项目名以「东涌」「名美」等连续汉字结尾，如「dg-szcz-prd东涌;」中
    # 「涌;」前一个字符是汉字「东」，不会被本正则命中；只有当单个汉字前面不是汉字
    # （而是英文字母/数字/分号/行首等，如「jy-szcz-prd东;」「mm-szcz-prd涌;」「;东;」
    # 或行首「东;」）、后面紧跟分号时，才说明该汉字被错误切断成一个孤立字段，此时命中。
    BROKEN_HANZI_PATTERN = re.compile(r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]);")

    # 校验项 2：负载参数行末尾的数字后直接拼接 "Error from server"。
    # 判定依据：正常第 4 段是纯数字并以换行结束；出现「数字 + Error from server」
    # 说明上报命令的出错信息被粘连到参数行，例如
    # "ms-zssc-prod乐涌;ms-global;30.829;325056608576Error from server (NotFound): ..."
    ERROR_GLUED_PATTERN = re.compile(r"[0-9]Error from server")

    @classmethod
    def extract_date_from_filename(cls, filename: str) -> Optional[str]:
        match = cls.FILENAME_PATTERN.search(filename)
        if match:
            return match.group(1)
        return None

    @classmethod
    def parse_line(cls, line: str) -> Optional[Tuple[str, NamespaceUsage]]:
        line = line.strip()
        if not line:
            return None

        parts = line.split(";")
        if len(parts) != 4:
            return None

        project_name = parts[0].strip()
        namespace = parts[1].strip()

        try:
            cpu_usage = float(parts[2].strip())
        except ValueError:
            cpu_usage = 0.0

        try:
            memory_bytes = float(parts[3].strip())
            memory_gb = memory_bytes / cls.BYTES_TO_GB
        except ValueError:
            memory_gb = 0.0

        namespace_usage = NamespaceUsage(
            namespace=namespace,
            cpu_usage=cpu_usage,
            memory_usage=memory_gb
        )

        return project_name, namespace_usage

    @classmethod
    def parse_file(cls, content: str) -> List[Tuple[str, List[NamespaceUsage]]]:
        project_data = {}

        for line in content.split("\n"):
            result = cls.parse_line(line)
            if result is None:
                continue

            project_name, namespace_usage = result

            if project_name not in project_data:
                project_data[project_name] = []

            project_data[project_name].append(namespace_usage)

        return list(project_data.items())

    @classmethod
    def read_and_parse(cls, filepath: str):
        path = Path(filepath)
        filename = path.name
        date = cls.extract_date_from_filename(filename)

        if not date:
            raise ValueError(f"Invalid filename format: {filename}")

        content = path.read_text(encoding="utf-8")
        project_data = cls.parse_file(content)

        return date, project_data

    @classmethod
    def validate_content(cls, content: str) -> List[str]:
        """对日报文件内容做上传前的前置校验。

        返回命中异常的描述列表（含行号与匹配片段），为空表示校验通过。
        该校验应在 parse_file 之前执行，命中任一异常即阻断上传与入库，
        避免断字/粘连错误污染解析与计算结果。
        """
        errors = []
        for line_no, line in enumerate(content.split("\n"), start=1):
            for match in cls.BROKEN_HANZI_PATTERN.finditer(line):
                errors.append(
                    f"第{line_no}行: 检测到单个汉字被断字成独立字段「{match.group(1)}」"
                    f"（片段: {cls._clip_line(line)}）"
                )
            for match in cls.ERROR_GLUED_PATTERN.finditer(line):
                errors.append(
                    f"第{line_no}行: 负载参数行末尾数字后直接拼接了 'Error from server'"
                    f"（片段: {cls._clip_line(line)}）"
                )
        return errors

    @staticmethod
    def _clip_line(line: str, limit: int = 60) -> str:
        """截取行片段用于异常提示，避免提示信息过长。"""
        line = line.strip()
        if len(line) <= limit:
            return line
        return line[:limit] + "..."
