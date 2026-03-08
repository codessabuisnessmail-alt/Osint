from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

# Import our modules
from tasks.celery_app import celery_app, scrape_profile_task, batch_scrape_task
from database.models import get_session, OSINTResult, Snapshot, ScrapingTask
from storage.s3_client import StorageClient
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FED Level OSINT System",
    description="Advanced OSINT scraping system with bot detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class ScrapeRequest(BaseModel):
    url: HttpUrl
    platform: Optional[str] = None
    username: Optional[str] = None
    priority: Optional[int] = 1

class BatchScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    platform: Optional[str] = None
    priority: Optional[int] = 1

class ScrapeResponse(BaseModel):
    task_id: str
    status: str
    message: str
    url: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class OSINTResultResponse(BaseModel):
    id: int
    url: str
    platform: str
    username: Optional[str]
    confidence_score: float
    is_bot_detected: bool
    detection_method: Optional[str]
    created_at: str
    updated_at: str

# Dependency to get database session
def get_db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "FED Level OSINT System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        session = get_session()
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        session.close()
        
        # Check Redis connection
        import redis
        redis_client = redis.Redis(host='redis', port=6379, db=0)
        redis_client.ping()
        redis_client.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_profile(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Scrape a single social media profile"""
    try:
        # Create task
        task = scrape_profile_task.delay(
            str(request.url),
            request.platform,
            request.username,
            request.priority
        )
        
        # Save task to database
        session = get_session()
        db_task = ScrapingTask(
            task_id=task.id,
            url=str(request.url),
            platform=request.platform or "unknown",
            status="pending",
            priority=request.priority
        )
        session.add(db_task)
        session.commit()
        session.close()
        
        logger.info(f"Created scraping task {task.id} for {request.url}")
        
        return ScrapeResponse(
            task_id=task.id,
            status="queued",
            message="Scraping task created successfully",
            url=str(request.url)
        )
        
    except Exception as e:
        logger.error(f"Error creating scraping task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.post("/scrape/batch", response_model=ScrapeResponse)
async def batch_scrape_profiles(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """Scrape multiple social media profiles in batch"""
    try:
        # Create batch task
        task = batch_scrape_task.delay(
            [str(url) for url in request.urls],
            request.platform,
            request.priority
        )
        
        # Save batch task to database
        session = get_session()
        db_task = ScrapingTask(
            task_id=task.id,
            url=f"BATCH_{len(request.urls)}_URLS",
            platform=request.platform or "unknown",
            status="pending",
            priority=request.priority
        )
        session.add(db_task)
        session.commit()
        session.close()
        
        logger.info(f"Created batch scraping task {task.id} for {len(request.urls)} URLs")
        
        return ScrapeResponse(
            task_id=task.id,
            status="queued",
            message=f"Batch scraping task created for {len(request.urls)} URLs",
            url=f"BATCH_{len(request.urls)}_URLS"
        )
        
    except Exception as e:
        logger.error(f"Error creating batch scraping task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create batch task: {str(e)}")

@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a scraping task"""
    try:
        # Get task from Celery
        task = celery_app.AsyncResult(task_id)
        
        # Get task from database
        session = get_session()
        db_task = session.query(ScrapingTask).filter(ScrapingTask.task_id == task_id).first()
        session.close()
        
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update database task status
        if db_task.status != task.state:
            session = get_session()
            db_task.status = task.state
            if task.state == 'SUCCESS':
                db_task.completed_at = datetime.utcnow()
            elif task.state == 'FAILURE':
                db_task.error_message = str(task.info) if task.info else "Unknown error"
            session.commit()
            session.close()
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task.state,
            progress=None,
            result=None,
            error=None
        )
        
        # Add additional information based on task state
        if task.state == 'PROGRESS' and task.info:
            response.progress = task.info.get('progress')
        elif task.state == 'SUCCESS' and task.result:
            response.result = task.result
        elif task.state == 'FAILURE':
            response.error = str(task.info) if task.info else "Task failed"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@app.get("/results", response_model=List[OSINTResultResponse])
async def get_results(
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session = Depends(get_db_session)
):
    """Get OSINT results with optional filtering"""
    try:
        query = session.query(OSINTResult)
        
        if platform:
            query = query.filter(OSINTResult.platform == platform)
        
        results = query.order_by(OSINTResult.created_at.desc()).offset(offset).limit(limit).all()
        
        return [OSINTResultResponse(**result.to_dict()) for result in results]
        
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@app.get("/results/{result_id}")
async def get_result_detail(result_id: int, session = Depends(get_db_session)):
    """Get detailed information about a specific OSINT result"""
    try:
        result = session.query(OSINTResult).filter(OSINTResult.id == result_id).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Get associated snapshot
        snapshot = session.query(Snapshot).filter(Snapshot.osint_result_id == result_id).first()
        
        response = result.to_dict()
        if snapshot:
            response['snapshot'] = snapshot.to_dict()
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting result detail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get result detail: {str(e)}")

@app.get("/stats")
async def get_system_stats(session = Depends(get_db_session)):
    """Get system statistics"""
    try:
        # Count results by platform
        platform_stats = {}
        platforms = ['facebook', 'instagram', 'twitter', 'linkedin', 'github']
        
        for platform in platforms:
            count = session.query(OSINTResult).filter(OSINTResult.platform == platform).count()
            platform_stats[platform] = count
        
        # Count total results
        total_results = session.query(OSINTResult).count()
        
        # Count bot detections
        bot_detections = session.query(OSINTResult).filter(OSINTResult.is_bot_detected == True).count()
        
        # Count snapshots
        total_snapshots = session.query(Snapshot).count()
        
        # Get recent activity
        recent_results = session.query(OSINTResult).order_by(OSINTResult.created_at.desc()).limit(5).all()
        recent_activity = [result.to_dict() for result in recent_results]
        
        return {
            "total_results": total_results,
            "bot_detections": bot_detections,
            "total_snapshots": total_snapshots,
            "platform_stats": platform_stats,
            "recent_activity": recent_activity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

@app.delete("/results/{result_id}")
async def delete_result(result_id: int, session = Depends(get_db_session)):
    """Delete a specific OSINT result and associated snapshots"""
    try:
        result = session.query(OSINTResult).filter(OSINTResult.id == result_id).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Get associated snapshot
        snapshot = session.query(Snapshot).filter(Snapshot.osint_result_id == result_id).first()
        
        # Delete from storage if exists
        if snapshot:
            storage_client = StorageClient()
            try:
                if snapshot.screenshot_path:
                    storage_client.delete_file(snapshot.screenshot_path)
                # Note: HTML content is stored in database, not in storage
            except Exception as e:
                logger.warning(f"Failed to delete storage files: {e}")
        
        # Delete from database
        if snapshot:
            session.delete(snapshot)
        session.delete(result)
        session.commit()
        
        logger.info(f"Deleted result {result_id}")
        
        return {"message": "Result deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting result: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete result: {str(e)}")

@app.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms and their configurations"""
    config = Config()
    return {
        "platforms": config.PLATFORMS,
        "rate_limits": {
            "global": f"{config.REQUESTS_PER_MINUTE}/minute",
            "platforms": config.PLATFORMS
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
