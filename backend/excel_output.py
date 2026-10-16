"""Bounded-memory XLSX output with text-safe cells and explicit resource cleanup."""
from tempfile import SpooledTemporaryFile
from urllib.parse import quote
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


def append_text_row(worksheet, values):
    row=[]
    for value in values:
        if isinstance(value,str):
            from openpyxl.cell import WriteOnlyCell
            cell=WriteOnlyCell(worksheet,value=value)
            cell.data_type='s'
            row.append(cell)
        else:
            row.append(value)
    worksheet.append(row)


def workbook_response(workbook, filename):
    stream=SpooledTemporaryFile(max_size=1024*1024,mode='w+b')
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
            while chunk:=stream.read(64*1024):
                yield chunk
        finally:
            stream.close()

    return StreamingResponse(chunks(),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(filename)},background=BackgroundTask(stream.close))
