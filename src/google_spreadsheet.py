import gspread
from oauth2client.service_account import ServiceAccountCredentials
import env

# instructions: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

creds = ServiceAccountCredentials.from_json_keyfile_dict(env.api_keys['google_spreadsheet_keyfile_dict'], scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open(env.employees_spreadsheet_name).sheet1

# Extract and print all of the values
list_of_hashes = sheet.get_all_records()
list_of_values = sheet.get_all_values()
print(list_of_hashes)
print(list_of_values)