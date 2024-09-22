import xlsxwriter


class SheetNoCig:
    def __init__(self, book: xlsxwriter.Workbook, name):
        self._sheet = book.add_worksheet(name + '_duplicati')
        self._columns_map = []
        self._rows: list[dict] = []
    
    def add(self, line: dict) -> None:
        row = {}
        for column_name, column_value in line.items():
            column_name = column_name.upper()
            row[self._get_col_index(column_name)] = column_value
        self._rows.append(row)
        
    def close(self) -> None:
        for col_number, col_name in enumerate(self._columns_map):
            self._sheet.write(0, col_number, col_name)
        
        sheet_row_number = 1
        for row in self._rows:
            for col_number, value in row.items():
                self._sheet.write(sheet_row_number, col_number, value)
            sheet_row_number += 1
    
    def _get_col_index(self, name: str) -> int:
        if name not in self._columns_map:
            self._columns_map.append(name)
        
        return self._columns_map.index(name)
    