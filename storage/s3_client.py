import boto3
from minio import Minio
from minio.error import S3Error
import hashlib
import os
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger(__name__)

class StorageClient:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.bucket_name = self.config.S3_BUCKET
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize either MinIO or S3 client based on endpoint"""
        try:
            if 'localhost' in self.config.S3_ENDPOINT or '127.0.0.1' in self.config.S3_ENDPOINT:
                # Use MinIO client
                self.client = Minio(
                    self.config.S3_ENDPOINT.replace('http://', '').replace('https://', ''),
                    access_key=self.config.S3_ACCESS_KEY,
                    secret_key=self.config.S3_SECRET_KEY,
                    secure=False
                )
                logger.info("Initialized MinIO client")
            else:
                # Use S3 client
                self.client = boto3.client(
                    's3',
                    endpoint_url=self.config.S3_ENDPOINT,
                    aws_access_key_id=self.config.S3_ACCESS_KEY,
                    aws_secret_access_key=self.config.S3_SECRET_KEY,
                    region_name=self.config.S3_REGION
                )
                logger.info("Initialized S3 client")
            
            self._ensure_bucket_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize storage client: {e}")
            raise
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            if hasattr(self.client, 'bucket_exists'):
                # MinIO client
                if not self.client.bucket_exists(self.bucket_name):
                    self.client.make_bucket(self.bucket_name)
                    logger.info(f"Created MinIO bucket: {self.bucket_name}")
            else:
                # S3 client
                try:
                    self.client.head_bucket(Bucket=self.bucket_name)
                except:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created S3 bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise
    
    def store_html_snapshot(self, html_content, filename):
        """Store HTML content as a file"""
        try:
            html_hash = hashlib.sha256(html_content.encode()).hexdigest()
            key = f"html/{filename}_{html_hash[:8]}.html"
            
            if hasattr(self.client, 'put_object'):
                # MinIO client
                self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=key,
                    data=html_content.encode(),
                    length=len(html_content.encode()),
                    content_type='text/html'
                )
            else:
                # S3 client
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=html_content.encode(),
                    ContentType='text/html'
                )
            
            logger.info(f"Stored HTML snapshot: {key}")
            return key, html_hash
            
        except Exception as e:
            logger.error(f"Failed to store HTML snapshot: {e}")
            raise
    
    def store_screenshot(self, screenshot_path, filename):
        """Store screenshot file"""
        try:
            if not os.path.exists(screenshot_path):
                raise FileNotFoundError(f"Screenshot file not found: {screenshot_path}")
            
            with open(screenshot_path, 'rb') as f:
                screenshot_data = f.read()
            
            screenshot_hash = hashlib.sha256(screenshot_data).hexdigest()
            key = f"screenshots/{filename}_{screenshot_hash[:8]}.png"
            
            if hasattr(self.client, 'put_object'):
                # MinIO client
                self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=key,
                    data=screenshot_data,
                    length=len(screenshot_data),
                    content_type='image/png'
                )
            else:
                # S3 client
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=screenshot_data,
                    ContentType='image/png'
                )
            
            logger.info(f"Stored screenshot: {key}")
            return key, screenshot_hash
            
        except Exception as e:
            logger.error(f"Failed to store screenshot: {e}")
            raise
    
    def retrieve_file(self, key):
        """Retrieve a file from storage"""
        try:
            if hasattr(self.client, 'get_object'):
                # MinIO client
                response = self.client.get_object(bucket_name=self.bucket_name, object_name=key)
                return response.read()
            else:
                # S3 client
                response = self.client.get_object(Bucket=self.bucket_name, Key=key)
                return response['Body'].read()
                
        except Exception as e:
            logger.error(f"Failed to retrieve file {key}: {e}")
            raise
    
    def delete_file(self, key):
        """Delete a file from storage"""
        try:
            if hasattr(self.client, 'remove_object'):
                # MinIO client
                self.client.remove_object(bucket_name=self.bucket_name, object_name=key)
            else:
                # S3 client
                self.client.delete_object(Bucket=self.bucket_name, Key=key)
            
            logger.info(f"Deleted file: {key}")
            
        except Exception as e:
            logger.error(f"Failed to delete file {key}: {e}")
            raise
    
    def list_files(self, prefix=""):
        """List files in storage with optional prefix"""
        try:
            files = []
            if hasattr(self.client, 'list_objects'):
                # MinIO client
                objects = self.client.list_objects(bucket_name=self.bucket_name, prefix=prefix, recursive=True)
                for obj in objects:
                    files.append(obj.object_name)
            else:
                # S3 client
                paginator = self.client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            files.append(obj['Key'])
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise
    
    def get_file_url(self, key, expires_in=3600):
        """Get a presigned URL for a file"""
        try:
            if hasattr(self.client, 'presigned_get_object'):
                # MinIO client
                return self.client.presigned_get_object(bucket_name=self.bucket_name, object_name=key, expires=expires_in)
            else:
                # S3 client
                return self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expires_in
                )
                
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {key}: {e}")
            raise
