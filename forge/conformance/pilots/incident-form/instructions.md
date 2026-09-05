# Incident report form: completion instructions

Read the case document and complete the form.

1. Output a single JSON object containing exactly the keys defined by the form schema, and no other text.
2. `reporter_name` is the full name of the person who made the report, exactly as written in the document.
3. `subject_name` is the full name of the person the incident happened to, exactly as written in the document.
4. `date_of_birth` is the subject's date of birth in ISO 8601 format YYYY-MM-DD.
5. `incident_date` is the date of the incident in ISO 8601 format YYYY-MM-DD.
6. `incident_time` is the 24-hour time HH:MM at which the incident occurred; omit this key entirely when the document states no time.
7. `phone` is the reporter's contact number normalised to E.164 with the +61 country code and no spaces or punctuation.
8. `site` is the place where the incident occurred as named in the document, in at most 60 characters.
9. `severity` is one of low, medium, or high: any injury means at least medium, and hospital treatment means high.
10. `injury_reported` is true when the document reports any injury to the subject, otherwise false.
11. `summary` restates what happened in the reporter's own words, in at most 200 characters.
