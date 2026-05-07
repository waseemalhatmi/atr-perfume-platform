# scripts/standalone_sync.py
"""
Professional Standalone Sync Runner for GitHub Actions.
This script initializes the Flask app context and executes the AdmitadService
sync logic for all stores configured for automatic synchronization.
"""

import os
import sys
import logging

# ── 1. Setup Environment & Paths ─────────────────────────────────────────────
# Add project root to sys.path so we can import 'app'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Configure logging for GitHub Actions console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("standalone_sync")

def run_external_sync():
    logger.info("==================================================")
    logger.info("🚀 STARTING EXTERNAL SYNC RUNNER (GitHub Actions)")
    logger.info("==================================================")

    try:
        from app import create_app
        from app.extensions import db
        from app.models import Store
        from app.services.admitad_service import AdmitadService
    except ImportError as e:
        logger.error(f"❌ Failed to import app components: {e}")
        sys.exit(1)

    # Initialize Flask app context
    # This allows us to use SQLAlchemy models and services directly
    app = create_app()
    
    with app.app_context():
        # ── 2. Identify Stores ────────────────────────────────────────────────
        stores = Store.query.filter_by(is_auto_sync=True).all()
        
        if not stores:
            logger.info("ℹ️ No stores found with 'is_auto_sync=True'. Skipping.")
            return

        logger.info(f"📋 Found {len(stores)} store(s) to synchronize.")

        total_success = 0
        total_failed = 0

        # ── 3. Execute Synchronization ────────────────────────────────────────
        for store in stores:
            logger.info(f"--- Synchronizing Store: {store.name} (ID: {store.id}) ---")
            
            try:
                # We reuse the exact same service logic used in the web UI
                success, message = AdmitadService.sync_store_feed(store.id)
                
                if success:
                    # Update the new professional tracking field
                    from datetime import datetime
                    store.last_external_sync = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"✅ SUCCESS: {message}")
                    total_success += 1
                else:
                    logger.error(f"❌ FAILED: {message}")
                    total_failed += 1
                    
            except Exception as e:
                logger.error(f"💥 CRITICAL ERROR during store sync: {str(e)}")
                total_failed += 1

        # ── 4. Summary ────────────────────────────────────────────────────────
        logger.info("==================================================")
        logger.info("🏁 SYNC RUNNER COMPLETED")
        logger.info(f"   - Total Stores Processed: {len(stores)}")
        logger.info(f"   - Successful: {total_success}")
        logger.info(f"   - Failed:     {total_failed}")
        logger.info("==================================================")

if __name__ == "__main__":
    run_external_sync()
