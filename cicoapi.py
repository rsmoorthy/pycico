"""
Read/Write data from CICO. CICO provides an easy way to generate API, without writing code on the CICO end.

The steps are as follows:
1. Login to CICO as Admin and go to Admin -> Manage Grid
2. Create a new grid/report.
    a. Add appropriate fields to be shown as the output of the API (Columns Tab)
    b. Add appropriate Filters to restrict the data (based on say programName etc) (Std Filters)
    c. IMPORTANT: If you want to write any field, set Inline Editable to Yes and ALWAYS set the roles who can actually edit. (Properties Tab)
3. Use the following example of python code to get data / update data

    
    import cicoapi

    USERNAME = "username@email.com"
    PASSWORD = "password"

    session, sid = cicoapi.login(USERNAME, PASSWORD)
    report = cicoapi.get_report(session, "Update Checkin Time")
    rows = cicoapi.get_rows(session, report)
    print("rows", rows)

    ret = cicoapi.set_fields(session, report, rows[0]["_id"], {"checkinDate": "05-07-2017 19:24:43"})

4. Another practical example.

    Let's say you want to set checkin time of some users. For a program, say, "Samyama Jan 2023". 
    It is assumed that the data is already there in CICO, and only the Checkin Date/Time needs to be updated.
    It is also assumed that the mobile number and name is matching exactly in CICO and your source.

    First create a Grid named "Checkin API for Samyama Jan 2023", Add columns, "Name, Mobile, Email, ProgramName, CheckinDate" (etc)
    Make "CheckinDate" field editable and allowed only for certain role (Better to create a new role/user only for this purpose)

    Follow the code above to login. After that,

    report = cicoapi.get_report(session, "Samyama Jan 2023")
    # records_to_checkin = [ {"name": "Moorthy RS", "mobile": "9980018517"}, 
                          {"name": "Murali", "mobile": "1234567890"} ]

    for record in records_to_checkin:
        rows = cicoapi.get_rows(session, report, condition=record)
        print("rows", rows) // You should get only one row here, since we are filtering based on name/mobile
        ret = cicoapi.set_fields(session, report, rows[0]["_id"], {"checkinDate": "05-07-2017 19:24:43"})
        # In case of checkin date/time, the format is dd-mm-yyyy hh:mm:ss
        print("result of set", ret)

5. Of course, if you want a generic Grid for multiple programs, you can set the program name in the get_rows condition field.

6. Limitations:

    a. This method can only be used, if all you need is **to update the field values. And no other action to trigger**
    b. Some error handling in this file could be better. (As of now, it is a kitchen sink code, but it works for most use cases)


"""
import requests
import json

# First do login. Returns session id
def login(username, password):
    """ Login to Cico using Username and Password

    Parameters:
    username (string): Specify the username -- usually in the form of an email id
    password (string): Specify the password

    Returns:
    A tuple of (session, SessionId)
    session (object): A session object that can be used to request to Cico directly
    SessionId (string): PHPSESSID returned by CICO

    You can use either one of the above to make further calls with Cico after authentication
    """

    session = requests.Session()
    resp = session.post("https://cico.isha.in/login.php", 
                    data={"username": username, "password": password, "do": "login", "submit": "Sign in"})
    if resp.status_code != 200:
        return None, None
    cookies = session.cookies.get_dict()
    return session, cookies["PHPSESSID"]

def get_report(session, report_name):
    """ Get report data

    Parameters:
    report_name (string): The name of the report or grid (as viewed in "Manage Grids")

    Returns:
    A dict of report containing
        report: various fields about report, that is used to send get/set requests
        report_name: The name of the report
        collname: The collection name

    The report data is passed to other functions get_rows an set_fields
    """

    data = {"collname": "reports", "condition": '{"name": "' + report_name + '"}', "rows": 1}
    resp = session.get("https://cico.isha.in/db2.php", params=data)

    if resp.status_code != 200:
        return None

    report = {}
    jresp = json.loads(resp.content)
    rep = jresp["rows"][0]
    rules = rep["filterRules"]
    # In the form like [{'name': 'R1', 'col': 'programName', 'match': 'isoneof', 'val': ['Ashramites'], 'link': 'and', 'prec': '1'}, {'name': 'R2', 'col': 'name', 'match': '=', 'val': 'G Kumaran'}]
    report["condition"] = {}
    for rule in rules:
        if rule["match"] == "=":
            report["condition"][rule["col"]] = rule["val"]
        if rule["match"] == "isoneof":
            report["condition"][rule["col"]] = {"$in": rule["val"]}

    report["fields"] = {}
    for colname in jresp["rows"][0]["gridColNames"]:
        report["fields"][colname] = 1

    report["context"] = {"collection": rep["db"]}

    return {"report": report, "report_name": report_name, "collname": rep["db"]}

def convert_report(report, rows=10):
    ''' Convert the report, so that it can be sent to get_rows, set_fields '''

    result = {"rows": rows, "page": 1, "sidx": "_id", "sord": "asc", "_search": "false", "splice": "none", "hook": "", "hookArgs": ""}
    for f in ["condition", "fields", "context"]:
        result[f] = json.dumps(report[f])

    return result

def get_rows(session, report, condition={}):
    """ Gets data given the session and report

    Parameters:
    session (object): Passed by login
    report (object): Returned by get_report
    condition (dict): If you want to add additional condition, you can specify here

    Returns:
    rows (array): Number of rows returned for this query
    """

    params = {"collname": report["collname"], "reportname": report["report_name"]}
    for key in condition:
        report["report"]["condition"][key] = condition[key]
    data = convert_report(report["report"])

    resp = session.post("https://cico.isha.in/db2.php", params=params, data=data)
    if resp.status_code != 200:
        return None

    jresp = json.loads(resp.content)
    return jresp["rows"]

def set_fields(session, report, id, fields):
    """ Sets certain fields to be updated with the values specified

    Parameters:
    session (object): Passed by login
    report (object): Returned by get_report
    id (string): The _id field that was returned from get_rows
    fields (dict): The field name and field value to be set

    Returns:
    "ok" on success, "error" or None on failures
    """

    params = {"collname": report["collname"], "reportname": report["report_name"], "oper": "edit"}
    data = { "context": report["report"]["context"], "keyfields": json.dumps(["_id"]), 
            "_id": id, "fieldnames": json.dumps(list(fields.keys()))}

    for f in fields:
        data[f] = fields[f]
    data["_id"] = id

    resp = session.post("https://cico.isha.in/db2.php", params=params, data=data)
    if resp.status_code != 200:
        return None

    jresp = json.loads(resp.content)
    if jresp["status"] != "ok":
        return jresp["status"] + ": " + jresp["message"]
    return jresp["status"]

