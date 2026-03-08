from celery import Celery
from config import Config
import logging

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'osint_tasks',
    broker=f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}',
    backend=f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}'
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
)

# Rate limiting per platform
celery_app.conf.task_routes = {
    'tasks.scraping_tasks.scrape_profile_task': {
        'queue': 'scraping',
        'rate_limit': '30/m'  # 30 requests per minute
    }
}

# Platform-specific rate limiting
PLATFORM_RATE_LIMITS = {
    'facebook': '20/m',    # 20 requests per minute
    'instagram': '15/m',   # 15 requests per minute
    'twitter': '25/m',     # 25 requests per minute
    'linkedin': '10/m',    # 10 requests per minute
}

@celery_app.task(bind=True)
def scrape_profile_task(self, url, platform=None, username=None, priority=1):
    """
    Celery task for scraping a social media profile
    
    Args:
        url (str): Profile URL to scrape
        platform (str): Platform name
        username (str): Username if known
        priority (int): Task priority (1-10)
    """
    try:
        logger.info(f"Starting scraping task for {url} on {platform}")
        
        # Import here to avoid circular imports
        from scraper.osint_scraper import OSINTScraper
        
        # Initialize scraper
        scraper = OSINTScraper()
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Scraping profile...', 'url': url}
        )
        
        # Perform scraping
        result = scraper.scrape_profile(url, platform, username)
        
        # Update task status
        self.update_state(
            state='SUCCESS',
            meta={'status': 'Completed', 'result': result}
        )
        
        # Clean up
        scraper.close()
        
        logger.info(f"Scraping task completed for {url}")
        return result
        
    except Exception as e:
        logger.error(f"Scraping task failed for {url}: {e}")
        
        # Update task status
        self.update_state(
            state='FAILURE',
            meta={'status': 'Failed', 'error': str(e)}
        )
        
        # Re-raise exception for Celery to handle
        raise
    
    finally:
        # Ensure scraper is closed
        try:
            if 'scraper' in locals():
                scraper.close()
        except:
            pass

@celery_app.task(bind=True)
def batch_scrape_task(self, urls, platform=None, priority=1):
    """
    Celery task for batch scraping multiple profiles
    
    Args:
        urls (list): List of profile URLs to scrape
        platform (str): Platform name
        priority (int): Task priority (1-10)
    """
    try:
        logger.info(f"Starting batch scraping task for {len(urls)} URLs on {platform}")
        
        results = []
        total_urls = len(urls)
        
        for i, url in enumerate(urls):
            try:
                # Update progress
                progress = (i / total_urls) * 100
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Scraping {i+1}/{total_urls}',
                        'progress': progress,
                        'current_url': url
                    }
                )
                
                # Scrape individual profile
                result = scrape_profile_task.delay(url, platform, None, priority)
                results.append({
                    'url': url,
                    'task_id': result.id,
                    'status': 'queued'
                })
                
                # Small delay between submissions
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error queuing task for {url}: {e}")
                results.append({
                    'url': url,
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Update final status
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'All tasks queued',
                'total_urls': total_urls,
                'results': results
            }
        )
        
        logger.info(f"Batch scraping task completed. Queued {len(results)} tasks.")
        return results
        
    except Exception as e:
        logger.error(f"Batch scraping task failed: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={'status': 'Failed', 'error': str(e)}
        )
        
        raise

@celery_app.task
def cleanup_old_snapshots():
    """Clean up old snapshots and results"""
    try:
        from datetime import datetime, timedelta
        from database.models import OSINTResult, Snapshot, get_session
        
        # Delete results older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        session = get_session()
        
        # Delete old snapshots first (due to foreign key constraints)
        old_snapshots = session.query(Snapshot).filter(
            Snapshot.created_at < cutoff_date
        ).all()
        
        for snapshot in old_snapshots:
            session.delete(snapshot)
        
        # Delete old results
        old_results = session.query(OSINTResult).filter(
            OSINTResult.created_at < cutoff_date
        ).all()
        
        for result in old_results:
            session.delete(result)
        
        session.commit()
        session.close()
        
        logger.info(f"Cleanup completed. Deleted {len(old_snapshots)} snapshots and {len(old_results)} results.")
        
        return {
            'deleted_snapshots': len(old_snapshots),
            'deleted_results': len(old_results)
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise

# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Clean up old snapshots every day at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_snapshots.s(),
        name='cleanup-old-snapshots'
    )

if __name__ == '__main__':
    celery_app.start()
