import sys
import xlsxwriter
import datetime

from configuration import Configuration
from extracted_line import ExtractedLine
from line_interpreter import LineInterpreter
from sheet_no_cig import SheetNoCig


class ResultSheet:
    def __init__(self, config: Configuration):
        self._config = config
        self._columns_map = ['nome_file']
        self._ignore_columns = config.get_columns_to_ignore()
        self._line_interpreter = LineInterpreter()
        self._workbook = xlsxwriter.Workbook('risultato.xlsx')
        # To format columns with dates later on
        self._date_format = self._workbook.add_format({'num_format': 'dd/mm/yyyy'})
        self._cig_worksheet = self._workbook.add_worksheet('CIG')
        self._removed_rows_worksheet = self._workbook.add_worksheet('cig_duplicati')
        # key is folder name
        self._sheets_no_cig: dict[str, SheetNoCig] = {} 
        # Widen columns, most are the dates one
        self._cig_worksheet.set_column('A:A', 20)
        self._cig_worksheet.set_column('E:E', 20)
        self._cig_worksheet.set_column('BV:BV', 20)
        self._cig_worksheet.set_column('O:O', 13)
        self._cig_worksheet.set_column('P:P', 13)
        self._cig_worksheet.set_column('AI:AI', 13)
        self._cig_worksheet.set_column('BI:BI', 13)
        self._cig_worksheet.set_column('BK:BK', 13)
        # {
        #    row_key: {
        #       column_key: column_value,
        #       column_key2: column_value2,
        #    },
        #    row_key2: {
        #       ...
        #    }
        #    ...
        # }
        self._cig_rows = {}
        self._cig_removed_rows = {}
        # {
        #     sheet_name: [ array of rows
        #         { row_stuff... },
        #     ]
        # }
        self._not_cig_removed_rows: dict[str, list[dict]] = {}
        # Used just to detect CIG duplicates
        # {
        #    'blablabla': {
        #        line_id = 'bla',
        #        last_update = datetime
        #    }
        # }
        self._cig = {}

    # Those are the CIGs lines, are thread special because we remove duplicates
    def add_line(self, line: ExtractedLine, file_name) -> None:
        # Manually add the file name in the first column of each row
        row = {self._columns_map.index('nome_file'): file_name}
        line_cig = None
        line_last_update = None
        for column_name, column_value in line.get().items():
            if column_name.upper() in self._ignore_columns:
                continue
            
            if column_name.upper() not in self._columns_map:
                self._columns_map.append(column_name.upper())
            sys.stdout.write("\rAggiungo linea " + line.id)
            sys.stdout.flush()
            row[self._columns_map.index(column_name.upper())] = column_value
            if column_name.upper() == 'CIG':
                line_cig = column_value

        if line_cig is not None and line_cig in self._cig.keys():
            self._cig_removed_rows[line.id] = row
        else:
            self._cig_rows[line.id] = row

        if line_cig is not None and line_cig not in self._cig.keys():
            self._cig[line_cig] = {
                'line_id': line.id,
                'last_update': line_last_update,  #TODO Have to remove this but wathcout for where its used
            }

    def add_not_cig_line(self, line: dict, folder_name: str) -> None:
        # First we find the CIG, if we have a main line with it, we save the line id
        main_line_id: str | None = None
        for column_name, column_value in line.items():
            column_name = column_name.upper()
            if column_name == 'CIG':
                if column_value in self._cig.keys():
                    main_line_id = str(self._cig[column_value]['line_id'])

        if main_line_id is None:
            return

        # Then we check if in cells we are going to write there is already data in, in that case we don't write the line
        # in the main sheet, but in the one for the removed lines
        found = False
        for column_name, column_value in line.items():
            column_name = column_name.upper()
            if column_name == 'CIG':
                continue
            if column_name in self._columns_map:
                column_key = self._columns_map.index(column_name)
                if (
                        column_key in self._cig_rows[main_line_id] and
                        self._cig_rows[main_line_id][column_key] == column_value
                ):
                    found = True
        if found:
            # If it doesn't exist yet, we create the sheet which will contain duplicate rows for this kind of lines       
            if folder_name not in self._sheets_no_cig:
                self._sheets_no_cig[folder_name] = SheetNoCig(self._workbook, folder_name)
            self._sheets_no_cig[folder_name].add(line)

            return

        # Lastly, if we have the main line, there wasn't already the same data, we add the new values
        for column_name, column_value in line.items():
            column_name = column_name.upper()
            if column_name not in self._columns_map:
                self._columns_map.append(column_name)
            sys.stdout.write("\rAggiungo informazioni aggiuntive alla linea " + main_line_id)
            sys.stdout.flush()
            self._cig_rows[main_line_id][self._columns_map.index(column_name)] = column_value

        return

    def close_file(self) -> None:
        # Write the column headers
        for col_number, col_name in enumerate(self._columns_map):
            self._cig_worksheet.write(0, col_number, col_name)
            self._removed_rows_worksheet.write(0, col_number, col_name)

        self._write_to_cig_sheet(self._cig_worksheet, self._cig_rows)
        self._write_to_cig_sheet(self._removed_rows_worksheet, self._cig_removed_rows)
        for sheet in self._sheets_no_cig.values():
            sheet.close()

        self._workbook.close()

    def _write_to_cig_sheet(self,
                            sheet: xlsxwriter.Workbook.worksheet_class,
                            rows: dict
                            ) -> None:
        sheet_row_number = 1
        for col_and_value in rows.values():
            for col_number, value in col_and_value.items():
                # Dedicated write for column with dates
                if self._line_interpreter.is_date(value):
                    sheet.write_datetime(
                        sheet_row_number,
                        col_number,
                        self._line_interpreter.get_date(value),
                        self._date_format
                    )
                else:
                    sheet.write(sheet_row_number, col_number, value)
            sheet_row_number += 1
