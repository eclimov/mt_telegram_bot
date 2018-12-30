import gspread
from oauth2client.service_account import ServiceAccountCredentials
import env


# instructions: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html

class GoogleSpreadsheetReader:
    # use creds to create a client to interact with the Google Drive API
    __scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self):
        self.__creds = ServiceAccountCredentials.from_json_keyfile_dict(
            env.google_spreadsheet_keyfile_dict,
            self.__scope
        )
        self.__client = gspread.authorize(self.__creds)

        # Find a workbook by name and open the first sheet
        # Make sure you use the right name here.
        self.sheet = self.__client.open(env.google_spreadsheet_name).sheet1

    def get_all_records(self):
        return self.sheet.get_all_records()

    def get_record_by_condition(self, key, value):
        records = self.get_all_records()
        for record in records:
            if key in record:
                if str(record[key]) == str(value):
                    return record
            else:
                return None
        return None


    def get_all_values(self):
        return self.sheet.get_all_values()
