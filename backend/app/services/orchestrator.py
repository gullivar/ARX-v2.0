import logging
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.pipeline import PipelineItem, CrawlResult, AnalysisResult, PipelineLog, PipelineStatus, PriorityLevel
from app.models.category import CategoryDefinition
from app.services.crawler_service import crawler_service
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.crawler = crawler_service
        self.is_running = False
        # Increase batch size for higher throughput, capitalizing on HTTPX speed
        self.crawl_batch_size = 30
        self.analysis_batch_size = 20
        
        # Monitoring
        self.start_time = datetime.now()
        self.last_run = {
            "crawl_loop": None,
            "analysis_loop": None
        }

    def get_status(self):
        return {
            "is_running": self.is_running,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.is_running else 0,
            "last_crawl_run": self.last_run["crawl_loop"],
            "last_analysis_run": self.last_run["analysis_loop"],
            "batch_sizes": {
                "crawl": self.crawl_batch_size,
                "analysis": self.analysis_batch_size
            }
        }
    def start(self):
        if not self.is_running:
            self.recover_on_startup()
            
            # Add separate jobs for decoupled processing
            # Reduced frequency to prevent DB Lock (SQLite) contention with API calls
            # Phase 1: Crawl
            self.scheduler.add_job(
                self.crawl_loop, 
                'interval', 
                seconds=10, 
                id='crawl_loop',
                max_instances=2
            )
            self.scheduler.add_job(self.analysis_loop, 'interval', seconds=5, max_instances=2)
            
            # Periodic LLM connection optimization (Every 5 mins)
            from app.services.llm_service import llm_service
            self.scheduler.add_job(llm_service.refresh_connection_status, 'interval', minutes=5)
            # Run once immediately
            llm_service.refresh_connection_status()
            
            self.scheduler.start()
            self.is_running = True
            
            # Load Policies
            from app.services.policy_service import policy_service
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, policy_service.load_policies)
            
            logger.info("Orchestrator started with decoupled pipelines (Crawl & Analysis).")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Orchestrator stopped.")

    def recover_on_startup(self):
        """
        Reset items stuck in active states from previous runs/crashes.
        """
        db = SessionLocal()
        try:
            # 1. Reset CRAWLING -> DISCOVERED (So they get picked up again)
            stuck_crawling = db.query(PipelineItem).filter(PipelineItem.status == PipelineStatus.CRAWLING).all()
            for item in stuck_crawling:
                item.status = PipelineStatus.DISCOVERED
                db.add(PipelineLog(item_id=item.id, stage="SYSTEM", level="WARNING", message="Reset from stuck CRAWLING state"))
            
            # 2. Reset ANALYZING -> CRAWLED_SUCCESS (So they get picked up by analysis loop)
            stuck_analyzing = db.query(PipelineItem).filter(PipelineItem.status == PipelineStatus.ANALYZING).all()
            for item in stuck_analyzing:
                item.status = PipelineStatus.CRAWLED_SUCCESS
                db.add(PipelineLog(item_id=item.id, stage="SYSTEM", level="WARNING", message="Reset from stuck ANALYZING state"))
                
            db.commit()
            if stuck_crawling or stuck_analyzing:
                logger.info(f"Recovery: Reset {len(stuck_crawling)} crawling and {len(stuck_analyzing)} analyzing items.")
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
        finally:
            db.close()

    async def crawl_loop(self):
        """
        Phase 1: DISCOVERED -> CRAWLING -> CRAWLED_SUCCESS (or FAIL)
        """
        self.last_run["crawl_loop"] = datetime.now()
        # print("[DEBUG] Crawl Loop Heartbeat")
        db = SessionLocal()
        try:
            # Fetch DISCOVERED items
            print("[DEBUG] Fetching DISCOVERED items...")
            items = db.query(PipelineItem).filter(
                PipelineItem.status == PipelineStatus.DISCOVERED
            ).order_by(
                PipelineItem.priority.asc(),
                PipelineItem.created_at.asc()
            ).limit(self.crawl_batch_size).all()

            if not items:
                print("[DEBUG] No items found to crawl.")
                return

            print(f"[DEBUG] Found {len(items)} items. Checking policies...")

            logger.info(f"--- Processing Crawl Batch: {len(items)} items ---")

            # Filter Blocked Items
            from app.services.policy_service import policy_service
            if not policy_service.oisd_loaded:
                policy_service.load_policies()
            
            valid_items = []
            for item in items:
                if policy_service.is_blocked(item.fqdn):
                    item.status = PipelineStatus.BLOCKED
                    db.add(PipelineLog(item_id=item.id, stage="POLICY", level="WARNING", message="Blocked by policy (OISD/DB)"))
                else:
                    item.status = PipelineStatus.CRAWLING
                    item.updated_at = datetime.now()
                    valid_items.append(item)
            
            db.commit()

            # Process concurrently
            if valid_items:
                logger.info(f"Executing crawl for {len(valid_items)} non-blocked items")
                tasks = []
                for item in valid_items:
                    tasks.append(self.process_crawl(item.id, item.fqdn))
                
                # Use return_exceptions to prevent one failure from killing all tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log any exceptions that occurred
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Crawl task {i} failed: {result}")
            else:
                logger.info("No valid items to crawl in this batch after policy filter.")

        except asyncio.CancelledError:
            logger.warning("Crawl loop was cancelled - shutting down gracefully")
            raise  # Re-raise to allow proper cleanup
        except Exception as e:
            logger.error(f"Crawl Loop Error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    async def process_crawl(self, item_id: int, fqdn: str):
        db = SessionLocal()
        try:
            url = f"https://{fqdn}"
            result = await self.crawler.crawl_page(url)
            
            content_path = None
            status = PipelineStatus.CRAWLED_FAIL
            
            if result.get("content"):
                data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/crawled")
                os.makedirs(data_dir, exist_ok=True)
                filename = f"{fqdn}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
                filepath = os.path.join(data_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(result["content"])
                
                content_path = f"data/crawled/{filename}"
                status = PipelineStatus.CRAWLED_SUCCESS
            
            # Update DB
            item = db.query(PipelineItem).filter(PipelineItem.id == item_id).first()
            if item:
                item.status = status
                item.updated_at = datetime.now()
                
                # Upsert CrawlResult
                existing_res = db.query(CrawlResult).filter(CrawlResult.item_id == item.id).first()
                if existing_res:
                    existing_res.url = result.get("url")
                    existing_res.http_status = result.get("status")
                    existing_res.html_content_path = content_path
                    existing_res.title = result.get("error") if result.get("error") else None
                    existing_res.crawled_at = datetime.now() # Update timestamp if schema has it, otherwise default update
                else:
                    crawl_res = CrawlResult(
                        item_id=item.id,
                        url=result.get("url"),
                        http_status=result.get("status"),
                        html_content_path=content_path,
                        title=result.get("error") if result.get("error") else None 
                    )
                    db.add(crawl_res)
                
                log = PipelineLog(
                    item_id=item.id,
                    stage="CRAWLER",
                    level="INFO" if status == PipelineStatus.CRAWLED_SUCCESS else "ERROR",
                    message=f"Crawl finished with status {result.get('status')}"
                )
                db.add(log)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to crawl item {item_id} ({fqdn}): {e}")
            db.rollback()
            try:
                item = db.query(PipelineItem).filter(PipelineItem.id == item_id).first()
                if item:
                    item.status = PipelineStatus.CRAWLED_FAIL
                    db.commit()
            except:
                pass
        finally:
            db.close()

    async def analysis_loop(self):
        """
        Phase 2: CRAWLED_SUCCESS -> ANALYZING -> COMPLETED
        """
        self.last_run["analysis_loop"] = datetime.now()
        # logger.info("[DEBUG] Analysis Loop Triggered")
        db = SessionLocal()
        try:
            items = db.query(PipelineItem).filter(
                PipelineItem.status == PipelineStatus.CRAWLED_SUCCESS
            ).order_by(
                PipelineItem.priority.asc(),
                PipelineItem.updated_at.asc()
            ).limit(self.analysis_batch_size).all()

            logger.info(f"[DEBUG] Analysis Loop found {len(items)} items")

            if not items:
                return

            # Mark as ANALYZING immediately to avoid double pickup
            for item in items:
                item.status = PipelineStatus.ANALYZING
                item.updated_at = datetime.now()
            db.commit()

            # Process concurrently (LLM calls are I/O bound on network)
            tasks = []
            for item in items:
                tasks.append(self.process_analysis(item.id, item.fqdn))
            
            if tasks:
                # Use return_exceptions to prevent one failure from killing all tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log any exceptions that occurred
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Analysis task {i} failed: {result}")

        except asyncio.CancelledError:
            logger.warning("Analysis loop was cancelled - shutting down gracefully")
            raise  # Re-raise to allow proper cleanup
        except Exception as e:
            logger.error(f"Analysis Loop Error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    async def process_analysis(self, item_id: int, fqdn: str):
        # Determine strict timeout for LLM task wrapper to prevent hanging forever
        try:
            await asyncio.wait_for(self._process_analysis_logic(item_id, fqdn), timeout=120)
        except asyncio.TimeoutError:
            logger.error(f"Analysis Task Timeout for {fqdn}")
            # Correct db status in a fresh session
            db = SessionLocal()
            try:
                item = db.query(PipelineItem).filter(PipelineItem.id == item_id).first()
                if item:
                    item.status = PipelineStatus.ANALYSIS_FAIL
                    db.add(PipelineLog(item_id=item.id, stage="LLM", level="ERROR", message="Analysis Task Timeout"))
                    db.commit()
            finally:
                db.close()

    async def _process_analysis_logic(self, item_id: int, fqdn: str):
        logger.info(f"Starting analysis logic for {item_id} ({fqdn})")
        db = SessionLocal()
        try:
            item = db.query(PipelineItem).filter(PipelineItem.id == item_id).first()
            if not item: 
                return

            # Need to read the content to send to LLM
            # We fetch the CrawlResult associated
            from app.models.pipeline import CrawlResult, AnalysisResult
            from app.services.llm_service import llm_service
            
            crawl_res = db.query(CrawlResult).filter(CrawlResult.item_id == item.id).first()
            if not crawl_res or not crawl_res.html_content_path:
                item.status = PipelineStatus.ANALYSIS_FAIL
                db.add(PipelineLog(item_id=item.id, stage="LLM", level="ERROR", message="No content found for analysis"))
                db.commit()
                return

            # Read content from file
            # content is saved in backend folder so we need absolute path logic or relative to cwd
            # orchestrator saves as data/crawled/... (relative to backend root usually)
            
            # Using simple read logic assuming cwd is backend root
            content = ""
            try:
                # Resolve path
                # Note: orchestrator.py L112: 
                # data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/crawled")
                # This goes up from services -> app -> backend -> data/crawled
                # Let's try to reconstruct
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                full_path = os.path.join(base_dir, crawl_res.html_content_path) 
                
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                item.status = PipelineStatus.ANALYSIS_FAIL
                db.add(PipelineLog(item_id=item.id, stage="LLM", level="ERROR", message=f"File read error: {e}"))
                db.commit()
                return

            # Call LLM
            # Note: llm_service.analyze_content IS synchronous (requests library), 
            # Fetch Category Definitions for LLM Context
            category_defs = {}
            try:
                cats = db.query(CategoryDefinition).all()
                for c in cats:
                    category_defs[c.name] = c.description
            except Exception as e:
                logger.warning(f"Failed to fetch category definitions: {e}")

            # so we should run it in an executor to avoid blocking the asyncio loop!
            # UPDATE: Using Async HTTPX client now for better concurrency
            logger.info(f"DEBUG: Processing {fqdn} via Async HTTPX...")
            try:
                analysis_data = await llm_service.analyze_content_async(fqdn, content, category_defs)
                logger.info(f"DEBUG: LLM returned for {fqdn}: {analysis_data is not None}")
            except Exception as e:
                 logger.error(f"DEBUG: Critical Error in Async LLM call for {fqdn}: {e}")
                 analysis_data = None

            if analysis_data:
                # Upsert AnalysisResult
                existing_analysis = db.query(AnalysisResult).filter(AnalysisResult.item_id == item.id).first()
                if existing_analysis:
                    existing_analysis.category_main = analysis_data.get("category_main", "Unknown")
                    existing_analysis.is_malicious = analysis_data.get("is_malicious", False)
                    existing_analysis.confidence_score = analysis_data.get("confidence_score", 0.0)
                    existing_analysis.summary = analysis_data.get("summary", "")
                    existing_analysis.llm_model_used = analysis_data.get("llm_model_used", "unknown")
                    existing_analysis.analyzed_at = datetime.now()
                else:
                    analysis_res = AnalysisResult(
                        item_id=item.id,
                        category_main=analysis_data.get("category_main", "Unknown"),
                        is_malicious=analysis_data.get("is_malicious", False),
                        confidence_score=analysis_data.get("confidence_score", 0.0),
                        summary=analysis_data.get("summary", ""),
                        llm_model_used=analysis_data.get("llm_model_used", "unknown")
                    )
                    db.add(analysis_res)
                
                item.status = PipelineStatus.COMPLETED
                item.completed_at = datetime.now()
                db.add(PipelineLog(item_id=item.id, stage="LLM", level="INFO", message=f"Classified as {analysis_data.get('category_main')}"))
                
                # --- Step 3: Index to Vector DB ---
                # TEMPORARILY DISABLED TO STABILIZE PIPELINE
                # try:
                #     from app.services.vector_service import vector_service
                #     rich_summary = f"Summary: {analysis_data.get('summary', '')}\n\nEvidence: {content[:1000]}"
                #     vector_service.add_item(
                #         fqdn=fqdn,
                #         content_summary=rich_summary,
                #         category=analysis_data.get("category_main", "Unknown"),
                #         is_malicious=analysis_data.get("is_malicious", False)
                #     )
                #     if 'analysis_res' in locals():
                #         analysis_res.vector_id = fqdn
                #     db.add(PipelineLog(item_id=item.id, stage="VECTOR", level="INFO", message="Indexed to KB"))
                # except Exception as ve:
                #     logger.error(f"Vector Indexing Failed for {fqdn}: {ve}")
                #     db.add(PipelineLog(item_id=item.id, stage="VECTOR", level="ERROR", message=f"Indexing failed: {ve}"))

            else:
                item.status = PipelineStatus.ANALYSIS_FAIL
                db.add(PipelineLog(item_id=item.id, stage="LLM", level="ERROR", message="LLM returned no data"))
            
            logger.warning(f"DEBUG: committing transaction for {fqdn}...")
            db.commit()
            logger.warning(f"DEBUG: transaction committed for {fqdn} (Status: {item.status})")

        except Exception as e:
            logger.error(f"Analysis Logic Error for {fqdn}: {e}")
            db.rollback()
            try:
                item = db.query(PipelineItem).filter(PipelineItem.id == item_id).first()
                if item:
                    item.status = PipelineStatus.ANALYSIS_FAIL
                    db.commit()
            except:
                pass
        finally:
            db.close()

orchestrator = Orchestrator()
