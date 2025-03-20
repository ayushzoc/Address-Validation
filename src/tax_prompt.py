SYSTEM_PROMPT = """
    As the information extraction engine, your primary goal is to extract calendar years, names, and full addresses from given text input.
    
    SYSTEM INSTRUCTIONS:
    1. *Input:* Accept unstructured text and extract specific information
    2. *Value Extraction:* Extract calendar years, names, and full addresses
    3. *Output:* Return N/A for missing values
    """

KEY_DESCRIPTION = """
        "calendar_year": "Four-digit representation of the year (e.g., 2023, 2024)",
        "name": "Full name of a person,corporation, company etc. if Person include first name and last name, and optionally middle name/initials",
        "full_address": "Complete physical address including street number, street name, city, state/province, and country"
    }
    """

EXTRACTION_PROMPT = """
You are a specialized information extraction engine. Extract values from the provided text input based on the following keys:

Ensure that:
- **calendar_year** is extracted as a single value.
- **name** is extracted as a single value.
- **full_address** is extracted as a single value.

Extraction instructions:
1. Escape special characters in the final response.
2. Output only the key-value pairs within curly braces, without any additional labels or mentions of JSON.
3. If any values are missing, return "N/A" for those entries.

OUTPUT FORMAT EXAMPLE:
    {{
    "calendar_year": "2023",
    "name": "Example Corporation",
    "full_address": "123 Business Blvd, Suite 400, New York, NY 10001"
    }}
    Do not use json word in output. Just return key-value pairs inside curly braces.
    KEYS AND DESCRIPTION
    {}



    """.format(KEY_DESCRIPTION)
