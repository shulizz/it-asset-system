"""Bounded-memory XLSX output with text-safe cells and explicit resource cleanup."""

import os
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from urllib.parse import quote

from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


@contextmanager
def export_workbook():
    """Own openpyxl's sheet files from the first header to final serialization."""
    from openpyxl import Workbook

    workbook = Workbook(write_only=True)
    try:
        yield workbook
    finally:
        # openpyxl 3.1.5 only removes sheet XML on a successful save.
        for sheet in workbook.worksheets:
            writer = sheet._writer
            if writer is not None and os.path.exists(writer.out):
                try:
                    if not sheet.closed:
                        sheet.close()
                finally:
                    writer.close()
                    writer.cleanup()
        workbook.close()


def append_text_row(worksheet, values):
    row = []
    for value in values:
        if isinstance(value, str):
            from openpyxl.cell import WriteOnlyCell
            from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

            value = ILLEGAL_CHARACTERS_RE.sub("", value)
            cell = WriteOnlyCell(worksheet, value=value)
            cell.data_type = "s"
            row.append(cell)
        else:
            row.append(value)
    worksheet.append(row)


def workbook_response(workbook, filename):
    stream = SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b")
    try:
        workbook.save(stream)
        stream.seek(0)
    except Exception:
        stream.close()
        raise
    finally:
        workbook.close()

    def chunks():
        try:
            while chunk := stream.read(64 * 1024):
                yield chunk
        finally:
            stream.close()

    return StreamingResponse(
        chunks(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(filename)},
        background=BackgroundTask(stream.close),
    )
