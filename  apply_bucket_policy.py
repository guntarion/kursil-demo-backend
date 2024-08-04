import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv
from datetime import datetime
import botocore
import uuid

load_dotenv()

# DigitalOcean Spaces Configuration
SPACES_REGION = os.getenv('SPACES_REGION')
SPACES_NAME = os.getenv('SPACES_NAME')
SPACES_ENDPOINT = f"https://{SPACES_REGION}.digitaloceanspaces.com"
SPACES_ACCESS_KEY = os.getenv('SPACES_ACCESS_KEY')
SPACES_SECRET_KEY = os.getenv('SPACES_SECRET_KEY')


def get_s3_client():
    return boto3.client('s3',
                        region_name=SPACES_REGION,
                        endpoint_url=SPACES_ENDPOINT,
                        aws_access_key_id=SPACES_ACCESS_KEY,
                        aws_secret_access_key=SPACES_SECRET_KEY,
                        config=Config(signature_version='s3v4'))

def check_file_exists(s3_client, bucket, object_name):
    try:
        s3_client.head_object(Bucket=bucket, Key=object_name)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise

def generate_unique_filename(original_filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    return f"{name}_{timestamp}{ext}"

def upload_file_to_spaces(file_path, folder="kursil/webresources"):
    s3_client = get_s3_client()
    file_name = os.path.basename(file_path)
    unique_file_name = generate_unique_filename(file_name)
    object_name = f"{folder}/{unique_file_name}"

    # Check if file already exists
    while check_file_exists(s3_client, SPACES_NAME, object_name):
        # If it exists, append a UUID to make it unique
        unique_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(unique_file_name)
        unique_file_name = f"{name}_{unique_id}{ext}"
        object_name = f"{folder}/{unique_file_name}"

    try:
        s3_client.upload_file(
            file_path, 
            SPACES_NAME, 
            object_name,
            ExtraArgs={'ACL': 'public-read'}
        )
        
        file_url = f"https://{SPACES_NAME}.{SPACES_REGION}.digitaloceanspaces.com/{object_name}"
        print(f"File uploaded successfully. Public URL: {file_url}")
        return file_url
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None

# Function to set ACL for an existing object
def set_object_acl_public(object_key):
    try:
        s3_client = get_s3_client()
        s3_client.put_object_acl(
            ACL='public-read',
            Bucket=SPACES_NAME,
            Key=object_key
        )
        print(f"ACL set to public-read for object: {object_key}")
    except Exception as e:
        print(f"Error setting ACL: {str(e)}")

if __name__ == "__main__":
    # Test upload
    test_file_path = "1_listof_topic.txt"
    uploaded_url = upload_file_to_spaces(test_file_path)
    
    # If you need to set ACL for an existing object
    # set_object_acl_public("kursil/webresources/existing_file.jpg")