from datetime import datetime
import re
import json 
import uuid
import os
def extract_year(date_string):
    """Extracts the year from a date string using multiple formats."""
    
    # List of common date formats to attempt parsing
    date_formats = [
        "%Y-%m-%d", "%Y-%d-%m", "%Y/%m/%d", "%Y/%d/%m",  # Year first
        "%m-%d-%Y", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"   # Month/Day/Year
    ]
    
    # Attempt parsing with strptime
    for date_format in date_formats:
        try:
            date_object = datetime.strptime(date_string, date_format)
            return date_object.year
        except ValueError:
            pass
    
    # If none of the formats work, use regex to capture the first 4-digit year
    year_pattern = r'\b(\d{4})\b'
    year_match = re.search(year_pattern, date_string)
    if year_match:
        return int(year_match.group(1))
    
    # Return None if no valid year could be extracted
    return None


def validate_tax_data_new(tax_data, relevant_tax_years, tax_years_present, tax_year_to_file):
    """Process tax data to categorize tax files into relevant and non-relevant groups."""
    
    relevant_taxes = []
    non_relevant_taxes = []
    current_year = datetime.now().year
    try:
        # Process tax data
        for tax in tax_data:
            tax_key = tax["tax_file"]
            tax_value = tax  # The tax data dictionary

            if tax_value.get("calendar_year") and tax_value["calendar_year"].isdigit():
                tax_year = int(tax_value["calendar_year"])
                tax_years_present.add(tax_year)
                tax_year_to_file.setdefault(tax_year, []).append(tax_key)

                # Determine relevancy
                relevancy_status = "Relevant" if tax_year in relevant_tax_years else "Non-Relevant"

                # Create structured tax file data
                tax_file_data = {
                    "tax_file": tax_key,
                    "doc_id": tax_value.get("doc_id"),  # File ID directly from the tax data
                    "calendar_year": tax_value.get("calendar_year"),
                    # "name": tax_value.get("name"),
                    # "full_address": tax_value.get("full_address"),
                    "relevancy_status": relevancy_status
                }

                # Categorize the tax document
                if relevancy_status == "Relevant":
                    relevant_taxes.append(tax_file_data)
                else:
                    non_relevant_taxes.append(tax_file_data)

        # Determine missing and present years
        missing_tax_years = relevant_tax_years - tax_years_present
        present_tax_years = relevant_tax_years - missing_tax_years

        # Generate the report
        time_period_validator_report = {
            "issues": {
                "issue_tag": "Time_Period_Validator",
                "issue_subtag": "tax_to_current_year",
                "missing_years": list(missing_tax_years),
                "non_relevant_tax_documents": [
                    {
                        "issue_id": int(uuid.uuid4().int % 1000),
                        "tax_file_name": tax["tax_file"],
                        "doc_id": tax["doc_id"],
                        "tax_year": tax["calendar_year"],
                        "relevancy_status": "Non-Relevant",
                        "message": f"The submitted tax file, ({tax['tax_file']}) does not align with the application form. The tax year ({tax['calendar_year']}) must fall within the two most recent tax years, which are {(current_year - 1)} and {(current_year - 2)}, based on the application form date ({current_year})."
                    } for tax in non_relevant_taxes
                ],
                # "relevant_tax_years": list(present_tax_years)
            },
            "details": {
                "relevant_tax_documents": relevant_taxes,  # Only Relevant in details
                # "relevant_tax_years": list(present_tax_years)
            }
        }

        # If all tax documents are relevant, provide a summary
        if not non_relevant_taxes:
            time_period_validator_report = {
                "details": {
                    "relevant_tax_documents": relevant_taxes,
                    # "relevant_tax_years": list(present_tax_years),
                    "message": "All tax documents are relevant."
                }
            }

    except Exception as e:
        raise ValueError(f"Error processing tax data: {e}")

    return time_period_validator_report

def validate_lease_to_rent_old(merged_data):
    """Validate the relevance of leases to rent rolls and return a structured report accordingly."""
    
    print("Inside Lease to Rent Validation")
    
    time_period_validator_report = {}

    try:
        for address, data in merged_data.items():
            rent_rolls = data.get("rent_roll", [])
            leases = data.get("leases", [])

            issues = []

            if not rent_rolls:
                issues.append({
                    "issue_id": uuid.uuid4().int % 1000,
                    "issue_tag": "Time_Period_Validator",
                    "issue_subtag": "lease_to_rent",
                    "missing_rent_roll": True,
                    "missing_lease": False,
                    "rent_roll_file_name": None,
                    "rent_roll_file_id": None,
                    "lease_file_name": None,
                    "lease_id": None,
                    "relevancy_status": "Missing Rent Roll"
                })
                time_period_validator_report[address] = {"issues": issues}
                continue

            for rent_roll in rent_rolls:
                rent_roll_date = datetime.strptime(rent_roll["data"]["date"], "%Y-%m-%d")
                rent_roll_file_name = rent_roll.get("rent_key")
                rent_roll_file_id = rent_roll.get("doc_id")

                if not leases:
                    issues.append({
                        "issue_id": uuid.uuid4().int % 1000,
                        "issue_tag": "Time_Period_Validator",
                        "issue_subtag": "lease_to_rent",
                        "missing_rent_roll": False,
                        "missing_lease": True,
                        "rent_roll_file_name": rent_roll_file_name,
                        "rent_roll_file_id": rent_roll_file_id,
                        "lease_file_name": None,
                        "lease_id": None,
                        "relevancy_status": "Missing Lease"
                    })
                    continue

                for lease in leases:
                    lease_start_date = datetime.strptime(lease["data"]["start_date"], "%Y-%m-%d")
                    lease_end_date = datetime.strptime(lease["data"]["end_date"], "%Y-%m-%d")
                    lease_file_name = lease.get("lease_key")
                    lease_id = lease.get("doc_id")

                    # Determine relevancy
                    relevancy_status = "Relevant" if lease_start_date <= rent_roll_date <= lease_end_date else "Non-Relevant"

                    # Add issue entry for each lease
                    issues.append({
                        "issue_id": uuid.uuid4().int % 1000,
                        "issue_tag": "Time_Period_Validator",
                        "issue_subtag": "lease_to_rent",
                        "missing_rent_roll": False,
                        "missing_lease": False,
                        "rent_roll_file_name": rent_roll_file_name,
                        "rent_roll_file_id": rent_roll_file_id,
                        "lease_file_name": lease_file_name,
                        "lease_id": lease_id,
                        "relevancy_status": relevancy_status,
                        "message":{
                             "impact": f"The submitted rent roll file, {rent_roll_file_name}, for the lease {lease_file_name} does not align with the lease period. The lease starts on {lease_start_date.date()} and ends on {lease_end_date.date()}, whereas the stated rent roll was prepared on {rent_roll_date.date()}.",
                            }
                        })

            if issues:
                time_period_validator_report[address] = {"issues": issues}

    except Exception as e:
        raise ValueError(f"Error validating lease-to-rent relevance: {e}")

    return time_period_validator_report

def validate_lease_to_rent_new(merged_data):
    """Validate the relevance of leases to rent rolls and return a structured report accordingly."""
    
    time_period_validator_report = {}

    try:
        for address, data in merged_data.items():
            rent_rolls = data.get("rent_roll", [])
            leases = data.get("leases", [])

            issues = []
            details = []  # To hold relevant leases

            if not rent_rolls:
                issues.append({
                    "issue_id": uuid.uuid4().int % 1000,
                    "issue_tag": "Time_Period_Validator",
                    "issue_subtag": "lease_to_rent",
                    "missing_rent_roll": True,
                    "missing_lease": False,
                    "rent_roll_file_name": None,
                    "rent_roll_file_id": None,
                    "lease_file_name": None,
                    "lease_id": None,
                    "relevancy_status": "Missing Rent Roll"
                })
                time_period_validator_report[address] = {"issues": issues, "details": details}
                continue

            for rent_roll in rent_rolls:
                rent_roll_date = datetime.strptime(rent_roll["data"]["date"], "%Y-%m-%d")
                rent_roll_file_name = rent_roll.get("rent_key")
                rent_roll_file_id = rent_roll.get("doc_id")

                if not leases:
                    issues.append({
                        "issue_id": uuid.uuid4().int % 1000,
                        "issue_tag": "Time_Period_Validator",
                        "issue_subtag": "lease_to_rent",
                        "missing_rent_roll": False,
                        "missing_lease": True,
                        "rent_roll_file_name": rent_roll_file_name,
                        "rent_roll_file_id": rent_roll_file_id,
                        "lease_file_name": None,
                        "lease_id": None,
                        "relevancy_status": "Missing Lease"
                    })
                    continue

                for lease in leases:
                    lease_start_date = datetime.strptime(lease["data"]["start_date"], "%Y-%m-%d")
                    lease_end_date = datetime.strptime(lease["data"]["end_date"], "%Y-%m-%d")
                    lease_file_name = lease.get("lease_key")
                    lease_id = lease.get("doc_id")

                    # Determine relevancy
                    relevancy_status = "Relevant" if lease_start_date <= rent_roll_date <= lease_end_date else "Non-Relevant"

                    issue_entry = {
                        "rent_roll_file_name": rent_roll_file_name,
                        "rent_roll_file_id": rent_roll_file_id,
                        "lease_file_name": lease_file_name,
                        "lease_id": lease_id,
                        "relevancy_status": relevancy_status
                    }

                    if relevancy_status == "Non-Relevant":
                        issue_entry.update({
                            "issue_id": uuid.uuid4().int % 1000,
                            "issue_tag": "Time_Period_Validator",
                            "issue_subtag": "lease_to_rent",
                            "message": f"The submitted rent roll file, ({rent_roll_file_name}), for the lease, ({lease_file_name}) does not align with the lease period. The lease starts on {lease_start_date.date()} and ends on {lease_end_date.date()}, while the rent roll was prepared on {rent_roll_date.date()}. Please ensure the rent roll corresponds to the correct lease dates."

                        })
                        issues.append(issue_entry)  # Non-relevant goes into issues
                    else:
                        details.append(issue_entry)  # Relevant goes into details

            if issues or details:
                time_period_validator_report[address] = {"issues": issues, "details": details}

    except Exception as e:
        raise ValueError(f"Error validating lease-to-rent relevance: {e}")

    return time_period_validator_report



# def validate_rent_to_tax_new_old(rent_roll_data, tax_data):
#     """Process rent roll data and categorize tax documents based on the rent year, including tax IDs."""
    
#     report = []
    
#     try:
#         # Loop through each rent roll data
#         for rent in rent_roll_data:
#             rent_key = rent["rent_key"]
#             rent_id = rent.get("doc_id")  # Rent roll doc ID
#             rent_date = rent["data"].get("date")  # Rent roll date
#             rent_year = extract_year(rent_date)  # Extract the year from the rent date
            
#             relevant_taxes = []
#             non_relevant_taxes = []

#             # Loop through each tax record and categorize based on the year
#             for tax in tax_data:
#                 tax_year = int(tax["calendar_year"])
                
#                 # If the tax year matches the rent year, it"s relevant
#                 if tax_year == rent_year:
#                     relevant_taxes.append({
#                         "tax_file": tax["tax_file"],
#                         "doc_id": tax.get("doc_id")
#                     })
#                 else:
#                     non_relevant_taxes.append({
#                         "tax_file": tax["tax_file"],
#                         "doc_id": tax.get("doc_id")
#                     })

#             # Prepare the issue report for the current rent roll
#             issue_id = int(uuid.uuid4().int % 1000)  # Generate a unique issue ID
#             time_period_validator_report = {
#                 "issues": {
#                     "issue_id": issue_id,
#                     "issue_tag": "Time_Period_Validator",
#                     "issue_subtag": "Rent-to-Tax",
#                     "rent_key": rent_key,
#                     "rent_id": rent_id,
#                     "rent_year": rent_year,
#                     "Relevant_tax": relevant_taxes,
#                     "Non_Relevant_Tax_Document": non_relevant_taxes,
#                     "message":{
#                         "impact": f"The submitted tax file {tax['tax_file']} does not align with the rent roll file {rent_key}. The rent roll year ({rent_year}) and tax year ({tax_year}) are different, but they should be the same.",
#                     }
#                 }
#             }

#             # Add the generated report to the list
#             report.append(time_period_validator_report)

#     except Exception as e:
#         raise ValueError(f"Error processing rent-to-tax data: {e}")

#     return report




def validate_rent_to_tax_old(rent_roll_data, tax_data):
    """Process rent roll data and categorize tax documents based on the rent year, including tax IDs."""
    
    report = []
    
    try:
        # Loop through each rent roll data
        for rent in rent_roll_data:
            rent_key = rent["rent_key"]
            rent_id = rent.get("doc_id")  # Rent roll doc ID
            
            # Validate rent date
            rent_date = rent["data"].get("date")
            if not rent_date:
                raise ValueError(f"Missing 'date' in rent roll data for rent_key: {rent_key}")

            rent_year = extract_year(rent_date)  # Extract the year from the rent date
            
            # Loop through each tax record and generate an issue for each tax file
            for tax in tax_data:
                tax_year = int(tax["calendar_year"])
                
                issue_id = int(uuid.uuid4().int % 1000)  # Generate a unique issue ID

                # Create an issue for each tax file
                time_period_validator_report = {
                    "issues": {
                        "issue_id": issue_id,
                        "issue_tag": "Time_Period_Validator",
                        "issue_subtag": "Rent-to-Tax",
                        "rent_key": rent_key,
                        "rent_id": rent_id,
                        "rent_year": rent_year,
                        "tax_file": tax["tax_file"],
                        "tax_year": tax_year,
                        "message": {
                            "impact": f"The submitted tax file {tax['tax_file']} does not align with the rent roll file {rent_key}. The rent roll year ({rent_year}) and tax year ({tax_year}) are different, but they should be the same."
                        }
                    }
                }

                # Add the generated report for this tax file to the list
                report.append(time_period_validator_report)

    except Exception as e:
        raise ValueError(f"Error processing rent-to-tax data: {e}")

    return report

def validate_rent_to_tax_new(rent_roll_data, tax_data):
    """Process rent roll data and categorize tax documents based on the rent year, including tax IDs."""
    
    time_period_validator_report = []  # To store the full report, including details and issues
    
    try:
        # Loop through each rent roll data
        for rent in rent_roll_data:
            rent_key = rent["rent_key"]
            rent_id = rent.get("doc_id")  # Rent roll doc ID
            
            # Validate rent date
            rent_date = rent["data"].get("date")
            if not rent_date:
                raise ValueError(f"Missing 'date' in rent roll data for rent_key: {rent_key}")

            rent_year = extract_year(rent_date)  # Extract the year from the rent date
            
            details = []  # To store relevant tax files for the current rent roll
            issues = []   # To store non-relevant tax files for the current rent roll
            
            # Loop through each tax record and generate an issue for each tax file
            for tax in tax_data:
                tax_year = int(tax["calendar_year"])
                
                # Determine relevancy
                relevancy_status = "Relevant" if rent_year == tax_year else "Non-Relevant"
                
                # Create a report entry for this tax file
                report_entry = {
                    "rent_key": rent_key,
                    "rent_id": rent_id,
                    "rent_year": rent_year,
                    "tax_file": tax["tax_file"],
                    "tax_year": tax_year,
                    "relevancy_status": relevancy_status
                }

                if relevancy_status == "Non-Relevant":
                    # If the tax file is non-relevant, add the extra details (issue_id, issue_tag, issue_subtag, and message)
                    report_entry.update({
                        "issue_id": int(uuid.uuid4().int % 1000),
                        "issue_tag": "Time_Period_Validator",
                        "issue_subtag": "Rent-to-Tax",
                        "message": f"The submitted tax file ({tax['tax_file']}) does not align with the rent roll file ({rent_key}). The rent roll year ({rent_year}) and tax year ({tax_year}) must match, but they differ. Please upload the correct tax file that aligns with the rent roll year."

                    })
                    issues.append(report_entry)  # Add to issues for non-relevant tax files
                else:
                    details.append(report_entry)  # Add to details for relevant tax files

            # Append the result for this rent roll to the time_period_validator_report
            time_period_validator_report.append({
                "rent_key": rent_key,
                "details": details,
                "issues": issues
            })

    except Exception as e:
        raise ValueError(f"Error processing rent-to-tax data: {e}")

    # Return the full time period validator report
    return time_period_validator_report




def transform_address_bucket(address_bucket):
    transformed_data = []

    for address, data in address_bucket.items():
        if "rent_roll" in data and data["rent_roll"]:
            rent_roll_entry = data["rent_roll"][0]  
            rent_key = rent_roll_entry["rent_key"]
            rent_doc_id = rent_roll_entry["doc_id"]

            leases = []
            lease_ids = []

            if "leases" in data:
                for lease in data["leases"]:
                    leases.append(lease["lease_key"])
                    lease_ids.append(lease["doc_id"])

            transformed_data.append({
                "rent_roll": rent_key,
                "rent_doc_id": rent_doc_id,
                "leases": leases,
                "lease_id": lease_ids
            })

    return transformed_data

def map_rent_id(rent_roll_data, file_id_to_map):
    mapped_rent_data = []
    for item in rent_roll_data:
        for rent_key,rent_value in item.items():
            rent_key = rent_key.split("/")[-1]
            file_name_without_extension = os.path.splitext(rent_key)[0]
            file_id = file_id_to_map.get(file_name_without_extension)
            
            if file_id:
                mapped_rent_data.append({
                    "rent_key": rent_key,
                    "data": rent_value,
                    "doc_id": file_id
                })
            else:
                mapped_rent_data.append({
                    "rent_key": rent_key,
                    "data": rent_value,
                    "doc_id": None
                })
    return mapped_rent_data

def map_tax_id(tax_data, file_id_to_map):
    """Map file names without extensions to their respective IDs."""
    mapped_tax_data = []

    try:
        for tax in tax_data:
            for tax_key, tax_value in tax.items():
                # Remove the file extension (if any)
                tax_key = tax_key.split("/")[-1]
                file_name_without_extension = os.path.splitext(tax_key)[0]
                
                # Look up the ID from file_id_to_map
                file_id = file_id_to_map.get(file_name_without_extension)
                
                if file_id:
                    mapped_tax_data.append({
                        "tax_file": tax_key,
                        "doc_id": file_id,
                        "calendar_year": tax_value.get("calendar_year"),
                        "name": tax_value.get("name"),
                        "full_address": tax_value.get("full_address")
                    })
                else:
                    mapped_tax_data.append({
                        "tax_file": tax_key,
                        "doc_id": None,  # If no ID found
                        "calendar_year": tax_value.get("calendar_year"),
                        "name": tax_value.get("name"),
                        "full_address": tax_value.get("full_address")
                    })

    except Exception as e:
        raise ValueError(f"Error mapping tax data to file IDs: {e}")

    return mapped_tax_data
