import os
import uuid
import json
import ast

from datetime import datetime
from collections import defaultdict
from sentence_transformers import SentenceTransformer
from rolls_lease_matcher.matcher_utility import *
from rolls_lease_matcher.address_validation import *
from rolls_lease_matcher.utility import normalize_string, normalize_address
from rolls_lease_matcher.count import *
from dateutil import parser



class Matcher:
    def __init__(self, lease_info, rent_roll_info, tax_info, id_mapped):
        self.lease_info = lease_info or []
        self.rent_roll_info = rent_roll_info or []
        self.tax_info = tax_info or []
        self.id_map = {id: filename for id, filename in id_mapped}
        self.file_to_id_mapping = {
            os.path.splitext(os.path.basename(filename))[0]: file_id
            for file_id, filename in self.id_map.items()
        }
        
        self.transformer = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    @classmethod
    def address_bucket_creation(cls, rent_json, lease_json, file_to_id_mapping):
        result = defaultdict(lambda: {"rent_roll": [], "leases": []})

        # Process rent roll data
        for rent_item in rent_json:
            for rent_key, rent_value in rent_item.items():
                rent_key = os.path.splitext(os.path.basename(rent_key))[0]
                rent_address = rent_value.get("property_address", "")
                rent_id = file_to_id_mapping.get(rent_key, None)

                result[rent_address]["rent_roll"].append(
                    {"rent_key": rent_key, "data": rent_value, "doc_id": rent_id}
                )

        # Process lease data
        for lease_item in lease_json:
            for lease_key, lease_value in lease_item.items():
                lease_key = os.path.splitext(os.path.basename(lease_key))[0]
                lease_address = lease_value.get("address", "")
                lease_id = file_to_id_mapping.get(lease_key, None)

                matched_address = next(
                    (rent_address for rent_address in result if compare_addresses(lease_address, rent_address)), None
                )

                if matched_address:
                    result[matched_address]["leases"].append(
                        {"lease_key": lease_key, "data": lease_value, "doc_id": lease_id}
                    )
                else:
                    result[lease_address]["leases"].append(
                        {"lease_key": lease_key, "data": lease_value, "doc_id": lease_id}
                    )

        return dict(result)
    
    @classmethod
    def missing_files(cls, address_bucket):
        missing_dict = {}
        
        def extract_units(doc_list, key):
            units = set()
            doc_map = defaultdict(list)
            for doc in doc_list:
                doc_units = cls.safe_eval(doc["data"].get(key, "[]"))
                for unit in doc_units:
                    units.add(unit)
                    doc_map[unit].append(doc["doc_id"])
            return units, doc_map
        
        for address, data in address_bucket.items():
            issues = []
            rent_units, rent_map = extract_units(data["rent_roll"], "unit_numbers")
            lease_units, lease_map = extract_units(data["leases"], "unit_number")
            
            for unit in rent_units - lease_units:
                issues.append(cls.generate_issue("missing_lease", rent_map[unit], unit))
            
            for unit in lease_units - rent_units:
                issues.append(cls.generate_issue("missing_rentroll", lease_map[unit], unit))
            
            if issues:
                missing_dict[address] = {"issues": issues}
        
        return missing_dict

    @staticmethod
    def generate_issue(issue_subtag, doc_ids, unit):
        return {
            "issue_id": uuid.uuid4().int % 10000,
            "issue_tag": "missing_document",
            "issue_subtag": issue_subtag,
            f"missing_{issue_subtag}": {"doc_id": doc_ids, "unit_number": unit},
            "message": f"{issue_subtag.replace('_', ' ').title()} identified for Unit {unit}.",
        }

    @staticmethod
    def safe_eval(value):
        try:
            return ast.literal_eval(value) if isinstance(value, str) else value
        except (ValueError, SyntaxError):
            return []

    def time_period_validator(self):
        result = {}

        # For tax to current year validation
        try:
            mapped_tax_data = map_tax_id(self.tax_info, self.file_to_id_mapping) if self.tax_info else {}
            if not mapped_tax_data:
                result["tax_to_current_year"] = {"error": "Tax Document is missing."}
            else:
                result["tax_to_current_year"] = validate_tax_data_new(mapped_tax_data, {datetime.now().year - 2, datetime.now().year - 1}, set(), {})
        except Exception as e:
            result["tax_to_current_year"] = {"error": f"An error occurred in tax validation: {str(e)}"}

        # For lease to rent validation
        try:
            if not (self.lease_info and self.rent_roll_info):
                result["lease_to_rent"] = {"error": "Lease or Rent Roll Document is missing."}
            else:
                result["lease_to_rent"] = validate_lease_to_rent_new(self.address_bucket_creation(self.rent_roll_info, self.lease_info, self.file_to_id_mapping))
        except Exception as e:
            result["lease_to_rent"] = {"error": f"An error occurred in lease-to-rent validation: {str(e)}"}

        # For rent to tax validation
        try:
            if not (self.rent_roll_info and self.tax_info):
                result["rent_to_tax"] = {"error": "Rentroll or Tax data is missing."}
            else:
                result["rent_to_tax"] = validate_rent_to_tax_new(map_rent_id(self.rent_roll_info, self.file_to_id_mapping), mapped_tax_data)
        except Exception as e:
            result["rent_to_tax"] = {"error": f"An error occurred in rent-to-tax validation: {str(e)}"}

        return result

    def check_missing_files(self, tags_list):
        """Check for missing files based on a predefined document list."""
        required_docs = {
            "Application form": "application_form",
            "T12 Document": "t12",
            "Personal Financial Statement": "pfs",
            "Purchase Agreement": "purchase_agreement",
            "Schedule of Real Estate Owned": "sreo",
            "Tax Returns": "tax_returns",
            "Preliminary Title": "title_prelims",
            "Lease Agreement": "lease_doc",
            "Rent Roll": "rent_roll",
        }

        missing_files = [
            {
                "issue_id": uuid.uuid4().int % 10000,
                "issue_tag": "missing_document",
                "issue_sub_tag": f"missing_{doc}",
                "message": f"Missing {doc} document.",
            }
            for doc, tag in required_docs.items() if tags_list.count(tag) == 0
        ]

        return missing_files
    
    def handle_missing_tax_year(self, validation_report):
        """Handles missing tax years by extracting issues from the validation report."""
        file_issues = []
        try:
            missing_tax_years = validation_report.get("tax_to_current_year", {}).get("issues", {}).get("missing_years", [])
        except Exception:
            missing_tax_years = []

        if missing_tax_years:
            file_issues.append({
                "issue_id": uuid.uuid4().int % 10000,
                "issue_tag": "missing_document",
                "issue_sub_tag": "missing_tax_year",
                "message": f"Missing tax document for the following year(s): {', '.join(map(str, missing_tax_years))}.",
            })
        
        return file_issues

    def match(self, tags_list):
        """Performs address bucketing, validation, and missing file checks."""
        if not self.lease_info and not self.rent_roll_info:
            return {
                "MAPPING RESULT": {},
                "MISSING REPORT": {},
                "TIME PERIOD VALIDATOR": {}
            }

        # Step 1: Process Address Bucketing
        address_bucket = self.address_bucket_creation(self.rent_roll_info, self.lease_info, self.file_to_id_mapping)

        # Step 2: Perform Validations & Reports
        mapping_result = transform_address_bucket(address_bucket)
        missing_report = self.missing_files(address_bucket)
        validation_report = self.time_period_validator()
        missing_files_report = self.check_missing_files(tags_list)

        # Step 3: Handle Missing Tax Year Separately
        file_issues = self.handle_missing_tax_year(validation_report)

        return {
            "mapping_result": mapping_result,
            "missing_report_on_property": missing_report,
            "document_version_validator": validation_report,
            "missing_files_on_deal": file_issues + missing_files_report
        }
