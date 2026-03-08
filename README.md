

A sophisticated OSINT (Open Source Intelligence) scraping system designed for law enforcement and intelligence gathering operations. This system uses advanced stealth techniques to avoid bot detection while gathering comprehensive profile data from social media platforms.

## 🏗️ Architecture Overview

### 1. Single Primary Browser Engine
- **Selenium with undetected-chromedriver** as the primary engine
- Plays nicer with dynamic pages and slower bot detection triggers
- Handles full page rendering, scrolling, and lazy-loaded content

### 2. JavaScript Rendering & Stealth
- Full page render with scrolling to load lazy content
- Cookie/local storage injection from previous sessions
- Full-page HTML snapshots + screenshots
- Random delays between requests to mimic human behavior

### 3. Advanced Bot Detection Analysis
- **Step 1**: Compare page structure (DOM selectors, titles, headers)
- **Step 2**: Compare error text and status codes (404 vs login redirect)
- **Step 3**: Visual hash checks for tricky pages
- **Confidence scoring** rather than absolute True/False detection

### 4. Asynchronous Task Management
- **Celery + Redis** for managing scraping tasks
- Platform-specific rate limiting to reduce bot detection risk
- Queue management with priority and retry logic

### 5. Data Storage & Management
- **PostgreSQL** for structured results (URLs, usernames, confidence scores)
- **MinIO/S3** for snapshots and screenshots
- Hash-based duplicate detection
- Automated cleanup of old data

## 🚀 Features

- **Multi-Platform Support**: Facebook, Instagram, Twitter, LinkedIn, GitHub
- **Real Name Lookup**: Advanced username generation and cross-platform name searching
- **Stealth Technology**: Undetected Chrome with advanced anti-detection
- **Intelligent Analysis**: Multi-layered bot detection analysis
- **Scalable Architecture**: Async task processing with Redis
- **Comprehensive Storage**: Database + object storage for all data
- **Web Interface**: FastAPI-based REST API for easy management
- **Monitoring**: Flower dashboard for Celery task monitoring
- **Docker Ready**: Complete containerized deployment

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Chrome browser (for local development)
- 8GB+ RAM recommended

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fed-level-osint
cp env.example .env
# Edit .env with your configuration
```

### 2. Start the System

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Access Services

- **Web API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Flower Dashboard**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Configuration

### Environment Variables

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=osint_db
POSTGRES_USER=osint_user
POSTGRES_PASSWORD=osint_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=osint-snapshots

# Browser
HEADLESS=true
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Rate Limiting
REQUESTS_PER_MINUTE=30
DELAY_MIN=2.0
DELAY_MAX=8.0
```

### Platform-Specific Settings

```python
PLATFORMS = {
    'facebook': {
        'base_url': 'https://www.facebook.com',
        'rate_limit': 20,        # 20 requests per minute
        'detection_threshold': 0.7
    },
    'instagram': {
        'base_url': 'https://www.instagram.com',
        'rate_limit': 15,        # 15 requests per minute
        'detection_threshold': 0.8
    },
    'twitter': {
        'base_url': 'https://twitter.com',
        'rate_limit': 25,        # 25 requests per minute
        'detection_threshold': 0.6
    },
    'linkedin': {
        'base_url': 'https://www.linkedin.com',
        'rate_limit': 10,        # 10 requests per minute
        'detection_threshold': 0.9
    }
}
```

## 📖 API Usage

### 1. Real Name Lookup

```bash
# Look up by name (generates usernames and searches)
python name_lookup_cli.py --name "John" "Doe" --birth-year 1990

# Look up by username
python name_lookup_cli.py --username "johndoe"

# Look up by email
python name_lookup_cli.py --email "johndoe@gmail.com"

# Reverse lookup (find usernames by name)
python name_lookup_cli.py --reverse "John Doe"
```

### 2. Scrape Single Profile

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.facebook.com/username",
    "platform": "facebook",
    "priority": 1
  }'
```

### 2. Batch Scraping

```bash
curl -X POST "http://localhost:8000/scrape/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.facebook.com/user1",
      "https://www.instagram.com/user2",
      "https://twitter.com/user3"
    ],
    "platform": "facebook"
  }'
```

### 3. Check Task Status

```bash
curl "http://localhost:8000/task/{task_id}"
```

### 4. Get Results

```bash
# All results
curl "http://localhost:8000/results"

# Platform-specific results
curl "http://localhost:8000/results?platform=facebook"

# System statistics
curl "http://localhost:8000/stats"
```

##  Real Name Lookup System

### Overview

The Real Name Lookup System integrates username generation with cross-platform profile searching to find real names and associated profiles across social media platforms. It also includes advanced cookie management to avoid login popups by importing and injecting existing browser cookies.

### Key Features

- **Username Generation**: Automatically generates potential usernames from first/last names and birth years
- **Cross-Platform Search**: Searches Facebook, Instagram, Twitter, LinkedIn, and GitHub simultaneously
- **Confidence Scoring**: Provides confidence scores for each found profile
- **Reverse Lookup**: Find usernames associated with real names
- **Email Integration**: Extract usernames from email addresses and search for profiles
- **Cookie Management**: Import cookies from browsers to avoid login popups
- **Selenium Stealth**: Advanced anti-detection browser automation

### Usage Examples

```python
from scraper.name_lookup import RealNameLookup

# Initialize the system
lookup = RealNameLookup()

# Generate usernames and search for profiles
result = lookup.lookup_by_name("John", "Doe", 1990)

# Search for real name by username
result = lookup.lookup_by_username("johndoe")

# Find usernames by name
result = lookup.reverse_lookup_by_name("John Doe")

# Search by email
result = lookup.lookup_by_email("johndoe@gmail.com")

# Import and inject cookies to avoid login popups
from scraper.cookie_manager import CookieManager
cookie_manager = CookieManager()

# Import cookies from Chrome
cookies = cookie_manager.import_cookies_from_browser('chrome', 'default')

# Inject cookies into Selenium session
with SeleniumStealthBrowser() as browser:
    cookie_manager.inject_cookies_to_selenium(browser, 'github')
    # Now browser session has GitHub cookies - no login popup!

### Confidence Scoring

- **HIGH (0.8+)**: Profile found on multiple platforms with consistent information
- **MEDIUM (0.6-0.8)**: Profile found on 2-3 platforms
- **LOW (0.4-0.6)**: Profile found on 1-2 platforms
- **VERY_LOW (<0.4)**: Limited or no profile information found

## 🍪 Cookie Management System

### Overview

The Cookie Management System automatically imports cookies from **the browser on the machine where the software runs** (Chrome, Firefox, Edge, Safari) and injects them into Selenium sessions to avoid login popups and maintain authenticated states across social media platforms.

> **Privacy Note:** Cookies are read locally from the user's own browser profiles on their machine. No cookies are bundled with the software or shared. Each person who runs this tool uses their own browser's cookies—not the developer's or anyone else's.

### Supported Browsers

- **Chrome**: Full cookie extraction from User Data profiles
- **Firefox**: Cookie extraction from Profiles directory
- **Edge**: Cookie extraction (Windows only)
- **Safari**: Basic support (macOS only)

### Key Features

- **Automatic Import**: Scans browser profiles for social media cookies
- **Cross-Platform**: Works with Facebook, Instagram, Twitter, LinkedIn, GitHub, TikTok
- **Smart Injection**: Automatically injects cookies into Selenium sessions
- **Profile Support**: Handles multiple browser profiles
- **Cookie Validation**: Ensures cookies are valid before injection

### Usage Examples

```python
from scraper.cookie_manager import CookieManager
from browser.selenium_stealth import SeleniumStealthBrowser

# Initialize cookie manager
cookie_manager = CookieManager()

# Import cookies from Chrome
chrome_cookies = cookie_manager.import_cookies_from_browser('chrome', 'default')

# Import from all available browsers
all_cookies = cookie_manager.import_all_browser_cookies()

# Start Selenium session with injected cookies
with SeleniumStealthBrowser() as browser:
    # Inject cookies for specific platform
    cookie_manager.inject_cookies_to_selenium(browser, 'github')
    
    # Or inject all platform cookies
    results = cookie_manager.inject_all_platform_cookies(browser)
    
    # Navigate to platform (should be logged in)
    browser.navigate_to('https://github.com')
```

### Cookie Summary

```python
# Get overview of available cookies
summary = cookie_manager.get_cookie_summary()
print(f"Total cookies: {summary['total_cookies']}")
print(f"Platforms: {list(summary['platforms_with_cookies'].keys())}")
```

## 🔍 Bot Detection Analysis

### Confidence Scoring System

- **HIGH (0.8+)**: Very likely real content
- **MEDIUM (0.6-0.8)**: Probably real content
- **LOW (0.4-0.6)**: Suspicious, possible bot detection
- **VERY_LOW (<0.4)**: Likely bot detection or error page

### Analysis Components

1. **Page Structure Analysis**
   - HTML structure validation
   - Content richness assessment
   - Social media element detection

2. **Error Indicator Analysis**
   - HTTP status codes
   - Error message detection
   - Redirect pattern analysis

3. **Bot Detection Pattern Analysis**
   - CAPTCHA detection
   - Security check pages
   - Rate limiting indicators

4. **Platform-Specific Analysis**
   - Login redirect detection
   - Profile content validation
   - Platform-specific error patterns

## 🐳 Docker Services

### Service Overview

- **postgres**: PostgreSQL 15 database
- **redis**: Redis 7 for Celery backend
- **minio**: S3-compatible object storage
- **celery_worker**: Background task processing
- **celery_beat**: Scheduled task management
- **web**: FastAPI web interface
- **flower**: Celery monitoring dashboard

### Service Management

```bash
# Start specific service
docker-compose up -d postgres redis

# View logs
docker-compose logs -f celery_worker

# Restart service
docker-compose restart web

# Scale workers
docker-compose up -d --scale celery_worker=3
```

## 🔒 Security Considerations

### Bot Detection Avoidance

- **User Agent Rotation**: Multiple realistic user agents
- **Viewport Variation**: Random viewport size changes
- **Timezone Randomization**: Geographic diversity simulation
- **Request Delays**: Human-like timing patterns
- **Stealth Scripts**: JavaScript injection to hide automation

### Rate Limiting

- **Global Limit**: 30 requests per minute
- **Platform Limits**: Varies by platform sensitivity
- **Exponential Backoff**: Automatic retry with delays
- **Queue Management**: Priority-based task processing

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# System health
curl "http://localhost:8000/health"

# Service status
docker-compose ps
```

### Log Management

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f celery_worker

# Export logs
docker-compose logs > osint_logs.txt
```

### Data Cleanup

- **Automatic**: Daily cleanup of old snapshots (30+ days)
- **Manual**: API endpoint for result deletion
- **Storage**: MinIO bucket management

## 🚨 Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   ```bash
   # Rebuild container
   docker-compose build --no-cache
   ```

2. **Database Connection**
   ```bash
   # Check PostgreSQL logs
   docker-compose logs postgres
   ```

3. **Redis Connection**
   ```bash
   # Restart Redis
   docker-compose restart redis
   ```

4. **Storage Issues**
   ```bash
   # Check MinIO console
   # http://localhost:9001
   ```

### Performance Tuning

- **Worker Scaling**: Increase `celery_worker` instances
- **Database**: Adjust PostgreSQL memory settings
- **Redis**: Configure persistence and memory limits
- **Browser**: Adjust viewport and headless settings

## 📈 Scaling & Production

### Production Considerations

- **Load Balancer**: Nginx for web service
- **SSL/TLS**: HTTPS termination
- **Monitoring**: Prometheus + Grafana
- **Backup**: Automated database and storage backups
- **Security**: Network isolation and access controls

### High Availability

- **Database**: PostgreSQL clustering
- **Redis**: Redis Sentinel or Cluster
- **Storage**: S3 with multiple regions
- **Workers**: Multiple Celery worker instances

## 📝 Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python -c "from database.models import create_tables; create_tables()"

# Run API
uvicorn api.main:app --reload

# Run Celery worker
celery -A tasks.celery_app worker --loglevel=info
```

### Code Structure

```
fed-level-osint/
├── api/                 # FastAPI web interface
├── browser/            # Stealth browser implementation
├── detection/          # Bot detection analysis
├── database/           # Database models and connections
├── storage/            # S3/MinIO storage client
├── scraper/            # Main OSINT scraper
├── tasks/              # Celery task definitions
├── config.py           # Configuration management
├── docker-compose.yml  # Service orchestration
├── Dockerfile          # Application container
└── requirements.txt    # Python dependencies
```

## 📄 License

This project is designed for authorized law enforcement and intelligence operations. Please ensure compliance with all applicable laws and regulations.

## 🤝 Support

For technical support or feature requests, please open an issue in the repository.

---

**⚠️ Disclaimer**: This tool is designed for authorized OSINT operations. Users are responsible for ensuring compliance with all applicable laws, terms of service, and ethical guidelines.
