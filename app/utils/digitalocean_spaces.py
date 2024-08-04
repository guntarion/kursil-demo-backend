# app/utils/digitalocean_spaces.py
import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

SPACES_REGION = os.getenv('SPACES_REGION')
SPACES_NAME = os.getenv('SPACES_NAME')
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"
SPACES_ACCESS_KEY = os.getenv('SPACES_ACCESS_KEY')
SPACES_SECRET_KEY = os.getenv('SPACES_SECRET_KEY')

def get_s3_client():
    return boto3.client('s3',
                        region_name=SPACES_REGION,
                        endpoint_url=f"https://{SPACES_REGION}.digitaloceanspaces.com",
                        aws_access_key_id=SPACES_ACCESS_KEY,
                        aws_secret_access_key=SPACES_SECRET_KEY,
                        config=Config(signature_version='s3v4'))


def upload_file_to_spaces(file_path, folder="kursil/webresources"):
    file_name = os.path.basename(file_path)
    object_name = f"{folder}/{file_name}"

    try:
        s3_client = get_s3_client()
        s3_client.upload_file(
            file_path, 
            SPACES_NAME, 
            object_name,
            ExtraArgs={'ACL': 'public-read'}
        )

        # Generate a public URL
        file_url = f"https://{SPACES_NAME}.{SPACES_REGION}.digitaloceanspaces.com/{object_name}"
        print(f"File uploaded successfully. URL: {file_url}")
        return file_url
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None



# if __name__ == "__main__":
#     # Test the upload function
#     test_file_path = "0_cost_rupiah.txt"
#     result = upload_file_to_spaces(test_file_path)
#     if result:
#         print(f"Test upload successful. File URL: {result}")
#     else:
#         print("Test upload failed.")    