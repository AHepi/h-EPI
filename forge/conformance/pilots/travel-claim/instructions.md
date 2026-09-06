# Travel claim form: completion instructions

Read the claim document and complete the form.

1. Output a single JSON object containing exactly the keys defined by the form schema, and no other text.
2. `claimant_name` is the full name of the employee making the claim, exactly as written in the document.
3. `approver_name` is the full name of the manager who approved the travel, exactly as written in the document; a person who is merely copied in or informed is not the approver.
4. `employee_id` is the claimant's employee number written as E- followed by its five digits, with any spaces or other separators removed.
5. `trip_start` is the departure date in ISO 8601 format YYYY-MM-DD.
6. `trip_end` is the return date in ISO 8601 format YYYY-MM-DD; a date the document fixes by a weekday or by an interval after another date counts as stated.
7. `nights_away` is the number of nights between the departure date and the return date, as an integer.
8. `destination_city` is the city where the work took place, in at most 40 characters; cities passed through in transit are not the destination.
9. `purpose` is one of conference, client_visit, training, fieldwork, or other, chosen from what the document says the travel was for.
10. `total_claimed_cents` is the total amount claimed in Australian dollars expressed in whole cents, so that $12.50 is 1250.
11. `advance_received` is true when the document says the claimant received a cash advance or up-front payment before travelling, otherwise false.
12. `receipts_attached` is true only when the document says every receipt is attached, and false when any receipt is missing or is to follow.
13. `contact_phone` is the claimant's own contact number normalised to E.164 with the +61 country code and no spaces or punctuation; numbers for hotels, airlines, training providers, or other people are not it.
14. `cost_centre` is the cost centre code as written in the document; omit this key entirely when the document states no cost centre.
15. `project_code` is the project code as written in the document; omit this key entirely when the document states no project code.
