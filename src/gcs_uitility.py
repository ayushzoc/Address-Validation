from google.cloud import storage
import os


def upload_file_to_gcs(bucket_name, local_file_path, destination_blob_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)

    print(f"File {local_file_path} uploaded to {destination_blob_name}.")
    
    
def upload_folder_to_gcs(bucket_name, local_folder_name, destination_blob_name, ext='.pdf'):
    for file_name in os.listdir(local_folder_name): 
        if file_name.endswith(ext):
            source_file_name = os.path.join(local_folder_name, file_name)
            gcs_blob_name = os.path.join(destination_blob_name, file_name)
            upload_file_to_gcs(bucket_name, source_file_name, gcs_blob_name)

    print("Folder uploaded sucessfully!!")
    
def delete_files_from_gcs_folder(bucket_name, gcs_folder_name, ext='.pdf'):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=gcs_folder_name)

    for blob in blobs:
        # print(blob.name)
        if blob.name.endswith(ext):
            blob.delete()
            print(f'Deleted: {blob.name}')
        
        
def list_files_in_gcs_folder(bucket_name, prefix=""):
    """Lists all files inside 'folders' (prefixes) in a GCS bucket."""
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=prefix, delimiter='/')
    print("Files in GCS folder:")
    files_in_gcs = [blob.name for blob in blobs]
    for file in files_in_gcs:
        print(file)
        
    print(f"Number of files in {prefix} = {len(files_in_gcs)}")
    
    return len(files_in_gcs)

def copy_file_in_gcs(source_bucket_name, source_blob_name, destination_bucket_name, destination_blob_name):
    client = storage.Client()

    # Get the source bucket and blob
    source_bucket = client.bucket(source_bucket_name)
    source_blob = source_bucket.blob(source_blob_name)

    # Get the destination bucket
    destination_bucket = client.bucket(destination_bucket_name)

    # Copy the blob
    source_bucket.copy_blob(source_blob, destination_bucket, destination_blob_name)

    print(f"Copied {source_blob_name} from {source_bucket_name} to {destination_blob_name} in {destination_bucket_name}")