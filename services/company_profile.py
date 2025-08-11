from db import execute_query

def get_company_profile():
    row = execute_query("SELECT name,address_line1,address_line2,city,phone,from_block FROM company_profile ORDER BY updated_at DESC LIMIT 1", dictionary=True)
    if not row:
        return {}
    return row[0]
