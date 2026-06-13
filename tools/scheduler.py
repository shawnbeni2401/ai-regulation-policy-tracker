import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scraper import run_scraper

def run_schedule_loop(interval_seconds=3600):
    """Runs a daemon loop that executes the scraper at regular intervals."""
    print(f"Starting Policy Tracker Scheduler Daemon...")
    print(f"Interval: {interval_seconds} seconds (approx. {interval_seconds / 3600:.2f} hours)")
    
    # Run once at startup
    print("\n--- Initial Scrape Run ---")
    try:
        run_scraper()
    except Exception as e:
        print("Initial scraper execution failed:", e)
        
    while True:
        try:
            print(f"Waiting for next schedule cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            time.sleep(interval_seconds)
            print("\n--- Scheduled Scrape Run ---")
            run_scraper()
        except KeyboardInterrupt:
            print("Scheduler daemon stopped by user.")
            break
        except Exception as e:
            print(f"Error in scheduler execution loop: {e}")
            time.sleep(60) # Wait a bit before retry in case of persistent errors

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        # Default to checking once every 12 hours if in daemon mode
        run_schedule_loop(12 * 3600)
    else:
        # Run immediately once and exit
        print("Running scraper once on demand...")
        updates = run_scraper()
        print(f"Done. Detected status updates: {len(updates)}")
