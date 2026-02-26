import re
from pathlib import Path
from typing import List, Tuple, Optional

from app.models import NamespaceUsage


class ReportParser:
    BYTES_TO_GB = 1024 * 1024 * 1024

    FILENAME_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

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
