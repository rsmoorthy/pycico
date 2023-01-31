# CICO API from python

## Overview
Read/Write data from CICO via API. CICO provides an easy way to generate API, **without writing code on the CICO end**

The steps are as follows:
1. Login to CICO as Admin and go to Admin -> Manage Grid
2. Create a new grid/report.
    a. Add appropriate fields to be shown as the output of the API (Columns Tab)
    b. Add appropriate Filters to restrict the data (based on say programName etc) (Std Filters)
    c. IMPORTANT: If you want to write any field, set Inline Editable to Yes and ALWAYS set the roles who can actually edit. (Properties Tab)

Please see the documentation inside cicoapi.py for writing code
