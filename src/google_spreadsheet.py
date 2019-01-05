import gspread
from oauth2client.service_account import ServiceAccountCredentials
import env


# instructions: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html

class GoogleSpreadsheetReader:
    # use creds to create a client to interact with the Google Drive API
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    SHEET_URL = env.google_spreadsheet_url

    def __init__(self):
        self._gc = None
        self._credentials = None

    @property
    def credentials(self):
        if self._credentials is None:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                env.google_spreadsheet_keyfile_dict,
                self.SCOPES
            )
            self._credentials = creds
        return self._credentials

    @property
    def gc(self):
        if self._gc is None:
            self._gc = gspread.authorize(self.credentials)
        return self._gc

    @property
    def sheet(self):
        if self.credentials.access_token_expired:
            self.gc.login()
        return self.gc.open_by_url(self.SHEET_URL).sheet1

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
