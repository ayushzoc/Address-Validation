# import vertexai

# from rolls_lease_matcher.extractor import Extractor
# import rolls_lease_matcher.lease_prompt as lease_prompt
# import rolls_lease_matcher.rent_roll_prompt as rental_prompt
# import rolls_lease_matcher.tax_prompt as tax_prompt
# from rolls_lease_matcher.gcs_uitility import *
# from rolls_lease_matcher.utility import *

# def matcher_extraction_pipeline():
#     BUCKET_NAME = "xtractrealestate"
#     GCS_LEASE_FOLDER = "lease_doc/"
#     GCS_RENTROLL_FOLDER = "rent_roll/"
#     GCS_TAX_FOLDER = 'tax_returns/'
#     #OUTPUT_FOLDER = "../outputs/"
#     #os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../credential/sandbox-230010-a8a2a7b265b5.json"
#     vertexai.init(project = "sandbox-230010", location = "us-central1")
    
#     lease_info = []
#     rentroll_info = []
#     tax_info = []
    
#     # Extraction from lease documents
#     lease_files_in_gcs = list_files_in_gcs_folder(BUCKET_NAME, GCS_LEASE_FOLDER)
#     if lease_files_in_gcs == 0:
#         print("NO LEASE FILES FOUND IN GCS")
#         print("NOT FOUND")
#     else:
#         print("LEASE FILES FOUND IN GCS")
    
#         print("\n\nEXTRACTING LEASE INFO...")
#         if True:
#         # try:
#             lease_extractor = Extractor(bucket_name = BUCKET_NAME, system_prompt = lease_prompt.SYSTEM_PROMPT)
#             lease_info = lease_extractor.extract(gcs_folder = GCS_LEASE_FOLDER, extraction_prompt = lease_prompt.EXTRACTION_PROMPT)
#         # except Exception as e:
#         #     print("EXCEPTION IN LEASE EXTRACTION!!!")
#         #     print(e)
    
#     # Extraction from rentroll documents
#     rentroll_files_in_gcs = list_files_in_gcs_folder(BUCKET_NAME, GCS_RENTROLL_FOLDER)
#     if rentroll_files_in_gcs == 0:
#         print("NO RENTROLL FILES FOUND IN GCS")
#         print("NOT FOUND")

#     else:
#         print("RENTROLL FILES FOUND IN GCS")
        
#         print("\n\nEXTRACTING RENTROLL INFO...")
#         if True:
#         # try:
#             rentroll_extractor = Extractor(bucket_name = BUCKET_NAME, system_prompt = rental_prompt.SYSTEM_PROMPT)
#             rentroll_info = rentroll_extractor.extract(gcs_folder = GCS_RENTROLL_FOLDER, extraction_prompt = rental_prompt.EXTRACTION_PROMPT)
#         # except Exception as e:
#         #     print("EXCEPTION IN RENTROLL EXTRACTION!!!")
#         #     print(e)


#     # Extraction from Tax documents
#     taxes_files_in_gcs = list_files_in_gcs_folder(BUCKET_NAME, GCS_TAX_FOLDER)
#     if taxes_files_in_gcs == 0:
#         print("NO TAX FILES FOUND IN GCS")
#     else:
#         print("TAX FILES FOUND IN GCS")
        
#         print("\n\nEXTRACTING TAX INFO...")
#         if True:
#         # try:
#             tax_extractor = Extractor(bucket_name = BUCKET_NAME, system_prompt = tax_prompt.SYSTEM_PROMPT)
#             tax_info = tax_extractor.extract(gcs_folder = GCS_TAX_FOLDER, extraction_prompt = tax_prompt.EXTRACTION_PROMPT)
#         # except Exception as e:
#         #     print("EXCEPTION IN RENTROLL EXTRACTION!!!")
#         #     print(e)
        
#     # Saving extracted data to json files
#     print("\n\nSAVING DATA TO JSON FILES...")
#     # save_json_file(lease_info, OUTPUT_FOLDER+"lease_info.json")
#     # save_json_file(rentroll_info, OUTPUT_FOLDER+"rentroll_info.json")
    
#     return lease_info, rentroll_info,tax_info
        
    
# if __name__ == "__main__":
#     matcher_extraction_pipeline()
import vertexai
import concurrent.futures

from rolls_lease_matcher.extractor import Extractor
import rolls_lease_matcher.lease_prompt as lease_prompt
import rolls_lease_matcher.rent_roll_prompt as rental_prompt
import rolls_lease_matcher.tax_prompt as tax_prompt
from rolls_lease_matcher.gcs_uitility import list_files_in_gcs_folder
from rolls_lease_matcher.utility import *

def extract_lease_info(bucket_name, gcs_folder):
    lease_files = list_files_in_gcs_folder(bucket_name, gcs_folder)
    if not lease_files:
        print(f"NO LEASE FILES FOUND IN GCS: {gcs_folder}")
        return []
    
    print(f"LEASE FILES FOUND IN GCS: {gcs_folder}\n\nEXTRACTING LEASE INFO...")
    lease_extractor = Extractor(bucket_name=bucket_name, system_prompt=lease_prompt.SYSTEM_PROMPT)
    return lease_extractor.extract(gcs_folder=gcs_folder, extraction_prompt=lease_prompt.EXTRACTION_PROMPT)

def extract_rentroll_info(bucket_name, gcs_folder):
    rentroll_files = list_files_in_gcs_folder(bucket_name, gcs_folder)
    if not rentroll_files:
        print(f"NO RENTROLL FILES FOUND IN GCS: {gcs_folder}")
        return []
    
    print(f"RENTROLL FILES FOUND IN GCS: {gcs_folder}\n\nEXTRACTING RENTROLL INFO...")
    rentroll_extractor = Extractor(bucket_name=bucket_name, system_prompt=rental_prompt.SYSTEM_PROMPT)
    return rentroll_extractor.extract(gcs_folder=gcs_folder, extraction_prompt=rental_prompt.EXTRACTION_PROMPT)

def extract_tax_info(bucket_name, gcs_folder):
    tax_files = list_files_in_gcs_folder(bucket_name, gcs_folder)
    if not tax_files:
        print(f"NO TAX FILES FOUND IN GCS: {gcs_folder}")
        return []
    
    print(f"TAX FILES FOUND IN GCS: {gcs_folder}\n\nEXTRACTING TAX INFO...")
    tax_extractor = Extractor(bucket_name=bucket_name, system_prompt=tax_prompt.SYSTEM_PROMPT)
    return tax_extractor.extract(gcs_folder=gcs_folder, extraction_prompt=tax_prompt.EXTRACTION_PROMPT)

def matcher_extraction_pipeline():
    BUCKET_NAME = "xtractrealestate"
    GCS_LEASE_FOLDER = "lease_doc/"
    GCS_RENTROLL_FOLDER = "rent_roll/"
    GCS_TAX_FOLDER = "tax_returns/"

    vertexai.init(project="sandbox-230010", location="us-central1")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_lease = executor.submit(extract_lease_info, BUCKET_NAME, GCS_LEASE_FOLDER)
        future_rentroll = executor.submit(extract_rentroll_info, BUCKET_NAME, GCS_RENTROLL_FOLDER)
        future_tax = executor.submit(extract_tax_info, BUCKET_NAME, GCS_TAX_FOLDER)

        lease_info = future_lease.result()
        rentroll_info = future_rentroll.result()
        tax_info = future_tax.result()

    print("\n\nSAVING DATA TO JSON FILES...")
    return lease_info, rentroll_info, tax_info

if __name__ == "__main__":
    matcher_extraction_pipeline()
