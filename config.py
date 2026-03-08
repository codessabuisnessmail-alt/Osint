import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'osint_db')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'osint_user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'osint_password')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', '6379')
    REDIS_DB = os.getenv('REDIS_DB', '0')
    
    # S3/MinIO Configuration
    S3_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', 'minioadmin')
    S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', 'minioadmin')
    S3_BUCKET = os.getenv('S3_BUCKET', 'osint-snapshots')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    # Toggle remote storage (S3/MinIO). When false, use fast local-disk storage only
    USE_REMOTE_STORAGE = os.getenv('USE_REMOTE_STORAGE', 'false').lower() == 'true'

    # Browser profile selection (to import cookies)
    EDGE_PROFILE = os.getenv('EDGE_PROFILE', 'default')
    CHROME_PROFILE = os.getenv('CHROME_PROFILE', 'default')
    
    # Browser Configuration
    CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', '')
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    VIEWPORT_WIDTH = int(os.getenv('VIEWPORT_WIDTH', '1920'))
    VIEWPORT_HEIGHT = int(os.getenv('VIEWPORT_HEIGHT', '1080'))
    
    # Stealth Configuration
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = int(os.getenv('REQUESTS_PER_MINUTE', '30'))
    DELAY_MIN = float(os.getenv('DELAY_MIN', '2.0'))
    DELAY_MAX = float(os.getenv('DELAY_MAX', '8.0'))
    
    # Detection Confidence Thresholds - Enhanced for better accuracy
    HIGH_CONFIDENCE = 0.85  # Increased from 0.8 for more stringent validation
    MEDIUM_CONFIDENCE = 0.65  # Increased from 0.6
    LOW_CONFIDENCE = 0.45  # Increased from 0.4
    
    # Platform-specific settings - Enhanced for better accuracy
    PLATFORMS = {
        'facebook': {
            'base_url': 'https://www.facebook.com',
            'rate_limit': 20,
            'detection_threshold': 0.75,  # Increased from 0.7
            'max_retries': 3,
            'timeout': 30,
            'confidence_boost': 0.1  # Additional confidence for successful extraction
        },
        'instagram': {
            'base_url': 'https://www.instagram.com',
            'rate_limit': 15,
            'detection_threshold': 0.85,  # Increased from 0.8
            'max_retries': 3,
            'timeout': 30,
            'confidence_boost': 0.05
        },
        'twitter': {
            'base_url': 'https://twitter.com',
            'rate_limit': 25,
            'detection_threshold': 0.7,  # Increased from 0.6
            'max_retries': 3,
            'timeout': 30,
            'confidence_boost': 0.1
        },
        'linkedin': {
            'base_url': 'https://www.linkedin.com',
            'rate_limit': 10,
            'detection_threshold': 0.95,  # Increased from 0.9 - most reliable
            'max_retries': 3,
            'timeout': 30,
            'confidence_boost': 0.15  # Highest boost for LinkedIn
        },
        'github': {
            'base_url': 'https://github.com',
            'rate_limit': 30,
            'detection_threshold': 0.8,  # Added GitHub configuration
            'max_retries': 3,
            'timeout': 30,
            'confidence_boost': 0.1
        }
    }
    
    # Enhanced validation settings
    VALIDATION = {
        'min_content_length': 100,  # Minimum content length for valid pages
        'min_social_elements': 2,   # Minimum social media elements for real accounts
        'max_error_indicators': 1,  # Maximum error indicators before marking as invalid
        'profile_indicators_weight': 0.3,  # Weight for profile indicators in confidence calculation
        'error_indicators_weight': 0.4,    # Weight for error indicators
        'structure_weight': 0.2,           # Weight for page structure
        'platform_specific_weight': 0.1    # Weight for platform-specific validation
    }
