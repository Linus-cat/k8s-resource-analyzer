from io import BytesIO
from typing import List
from openpyxl import Workbook

from app.models import ProjectUsage
from app.calculator import Calculator


class ExcelExporter:
    def __init__(self, calculator: Calculator):
        self.calculator = calculator

    def export(
        self, date: str, project_usages: List[ProjectUsage]
    ) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "Resource Usage Report"

        headers = ["云序号", "日期", "cpu使用率", "内存使用率"]
        ws.append(headers)

        formatted_date = self.calculator.format_date(date)

        for usage in project_usages:
            cloud_id = usage.cloud_id or ""
            cpu_rate = round(usage.cpu_rate / 100, 4) if usage.cpu_rate is not None else ""
            memory_rate = round(usage.memory_rate / 100, 4) if usage.memory_rate is not None else ""

            ws.append([cloud_id, formatted_date, cpu_rate, memory_rate])

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def export_multiple(
        self, reports: List[tuple[str, List[ProjectUsage]]]
    ) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "Resource Usage Report"

        headers = ["云序号", "日期", "cpu使用率", "内存使用率"]
        ws.append(headers)

        for date, project_usages in reports:
            formatted_date = self.calculator.format_date(date)

            for usage in project_usages:
                cloud_id = usage.cloud_id or ""
                cpu_rate = round(usage.cpu_rate / 100, 4) if usage.cpu_rate is not None else ""
                memory_rate = round(usage.memory_rate / 100, 4) if usage.memory_rate is not None else ""

                ws.append([cloud_id, formatted_date, cpu_rate, memory_rate])

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
