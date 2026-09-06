# Leave request form: completion instructions

Read the request and complete the form.

1. Output a single JSON object containing exactly the keys defined by the form schema, and no other text.
2. `employee_name` is the full name of the person requesting leave, exactly as written.
3. `leave_type` is one of annual, sick, carer, or unpaid, chosen from what the request says the leave is for.
4. `start_date` is the first day of leave in ISO 8601 format YYYY-MM-DD.
5. `end_date` is the last day of leave in ISO 8601 format YYYY-MM-DD.
6. `total_days` is the number of working days requested, as an integer.
7. `reason` restates the stated reason in at most 160 characters.
8. `manager_notified` is true when the request says the manager already knows, otherwise false.
