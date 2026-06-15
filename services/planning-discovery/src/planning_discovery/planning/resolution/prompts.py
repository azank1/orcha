"""Prompts for Stage 2b — IO resolution (capability selection and input extraction)."""

CAPABILITY_SELECTION_PROMPT = """\
Select the best capability for this task.

TASK: {task_description}

AVAILABLE CAPABILITIES:
{capabilities_json}

Return the index (0-based) of the best matching capability.
Output only the integer index, nothing else.\
"""

INPUT_EXTRACTION_PROMPT = """\
Extract input values from the user query for this capability.

USER QUERY: {user_query}

TASK CONTEXT: {task_description}

CAPABILITY INPUT SCHEMA:
{input_schema}

INSTRUCTIONS:
1. Extract values that are EXPLICITLY mentioned in the query
2. Do NOT guess or infer values
3. Use null for any value not found in the query
4. Match field names exactly as specified in schema

Examples:
Query: "Find flights from London to Tokyo on March 15th for 2 passengers"
Schema: {{origin, destination, departure_date, passengers}}
Output: {{
  "extracted_inputs": {{
    "origin": "London",
    "destination": "Tokyo",
    "departure_date": "2026-03-15",
    "passengers": 2
  }}
}}

Query: "Book a hotel in Shibuya"
Schema: {{location, check_in_date, num_nights, budget}}
Output: {{
  "extracted_inputs": {{
    "location": "Shibuya",
    "check_in_date": null,
    "num_nights": null,
    "budget": null
  }}
}}

Now extract for:
Query: {user_query}
Schema: {input_schema}

Output JSON:
{{
  "extracted_inputs": {{ ... }}
}}\
"""

FIELD_MATCHING_PROMPT = """\
Match the required input field to the best available output field.

REQUIRED INPUT FIELD:
  Name: {field_name}
  Type: {field_type}
  Description: {field_description}

AVAILABLE OUTPUT FIELDS FROM PREVIOUS TASKS:
{candidates_json}

INSTRUCTIONS:
1. Find the output field that SEMANTICALLY matches the required input
2. Consider field descriptions and context, not just names
3. Ensure type compatibility
4. If no semantically equivalent field exists, you MUST return null

GOOD MATCH examples (semantically equivalent):
- "cost" matches "price" or "total_amount" (same monetary value)
- "booking_id" matches "confirmation_number" or "reservation_id" (same booking reference)
- "destination_city" matches "city" or "location" (same place concept)
- "arrival_time" matches "check_in_date" (flight arrival used as hotel check-in)

BAD MATCH examples — return null for these (different domains or entities):
- "hotel_id" vs "cheapest_price" — a price is NOT a hotel identifier
- "guest_name" vs "flight_number" — a flight code is NOT a person's name
- "check_in_date" vs "origin_city" — a city is NOT a date
- "hotel_id" vs "flight_id" — different entity types, even if both are IDs

If you are not highly confident (>= 0.85) that the fields are semantically equivalent,
return null for matched_task_id.

Output JSON format:
{{
  "matched_task_id": "task_2" or null,
  "matched_field_name": "price" or null,
  "confidence": 0.95,
  "reasoning": "The 'price' field from hotel booking semantically matches 'cost' as both represent monetary amounts"
}}\
"""

PREREQUISITE_DETECTION_PROMPT = """\
Determine if a missing prerequisite task is needed to produce a required input field.

CURRENT TASK: {task_description}

REQUIRED INPUT FIELD:
  Name: {field_name}
  Type: {field_type}
  Description: {field_description}

PREVIOUS TASKS IN WORKFLOW:
{previous_tasks_json}

QUESTION: Is there a task missing from the workflow above that would naturally produce
"{field_name}" as an output, which could then be passed to "{task_description}"?

FIELD CATEGORIES — use these to decide:

NEVER triggers a prerequisite (always HITL / user-provided):
- Dates and times: departure_date, check_in, check_out, travel_date, arrival_date,
  booking_date, start_date, end_date
  (These come from the user's intent, not from another agent)
- Personal information: guest_name, guest_email, passenger_name, phone, address
- User preferences: budget, cabin_class, meal_preference, special_requests,
  max_price, min_rating, rooms
- Payment details: credit_card, payment_method, billing_address

COULD trigger a prerequisite (comes from a prior search / lookup result):
- Entity identifiers returned by a search: hotel_id, room_type_id, flight_id,
  property_id, listing_id, accommodation_id, offer_id
  (You need to run a search first to obtain these IDs)
- Computed or fetched values: exchange_rate, converted_price, availability_status
  (Require a lookup agent to obtain)

RULES:
- Answer YES only if a distinct, identifiable action (e.g., "search hotels",
  "get exchange rate") would clearly produce this field as output.
- Answer NO if the field belongs to the NEVER category above.
- Answer NO if any previous task already covers the capability needed.
- CIRCULARITY CHECK: if the current task is itself a search or discovery task
  (e.g. "search flights", "find hotels", "look up accommodation") and the missing
  field is an input users typically supply (e.g. departure_date, destination,
  passengers, occupancy), answer needs_prerequisite: false. A search agent does
  NOT need another search agent to obtain its own inputs.

Examples:

Case 1 — YES (missing search step):
  Current task: "book_hotel" needs field "hotel_id"
  Previous tasks: ["search_flights"]
  → needs_prerequisite: true, action: "search hotels", capability_hint: "hotel search"

Case 2 — NO (user should provide — personal info):
  Current task: "book_hotel" needs field "guest_name"
  Previous tasks: ["search_hotels"]
  → needs_prerequisite: false (guest_name is personal info, comes from the user)

Case 3 — NO (already covered):
  Current task: "book_hotel" needs field "hotel_id"
  Previous tasks: ["search_hotels"] (outputs include hotel_id)
  → needs_prerequisite: false (search_hotels already provides hotel_id)

Case 4 — YES (missing lookup step):
  Current task: "convert_currency" needs field "exchange_rate"
  Previous tasks: ["search_flights"]
  → needs_prerequisite: true, action: "get exchange rate", capability_hint: "currency exchange rate lookup"

Case 5 — NO (circularity guard — current task IS the search):
  Current task: "search_flights" needs field "departure_date"
  Previous tasks: []
  → needs_prerequisite: false (departure_date is user-supplied; creating another
    search_flights for the same input would cause a cycle)

Case 6 — NO (date field — always user-provided):
  Current task: "book_hotel" needs field "check_in"
  Previous tasks: ["search_hotels"]
  → needs_prerequisite: false (check_in is a date chosen by the user)

Output JSON:
{{
  "needs_prerequisite": true or false,
  "action_description": "search hotels in the destination city" or null,
  "capability_hint": "hotel search" or null,
  "reasoning": "Booking a hotel requires selecting a specific hotel first via a search step"
}}\
"""
