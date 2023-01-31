""" Please read the documentation inside cicoapi.py

This example uses and example Grid/Report called "Update Checkin Time", allowing 
checkinDate to be editable only by Admin
"""
## checkinDate 05-07-2017 19:24:46 mobile: 9940641399
import cicoapi


USERNAME = "userid@user.com"
PASSWORD = "password"

session, sid = cicoapi.login(USERNAME, PASSWORD)
report = cicoapi.get_report(session, "Update Checkin Time")
rows = cicoapi.get_rows(session, report)
print("rows", rows)

ret = cicoapi.set_fields(session, report, rows[0]["_id"], {"checkinDate": "05-07-2017 19:24:43" })
print("set checkinDate (should succeed)", ret) # this will return "ok"

ret = cicoapi.set_fields(session, report, rows[0]["_id"], {"mobile":"9940641399" })
print("set mobile (should fail)", ret) # this will return "error"
