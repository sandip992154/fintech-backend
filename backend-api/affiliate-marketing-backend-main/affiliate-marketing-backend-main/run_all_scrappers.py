import os
import sys
import subprocess
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed


# Set UTF-8 environment encoding for all operations
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"


# Calculate root directory and set absolute path to database folder under root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_ROOT = os.path.join(ROOT_DIR, "core")
OUTPUT_ROOT = os.path.join(ROOT_DIR, "core", "database")

# Reserve 2 cores for system - use remaining for scraping
MAX_WORKERS = max(1, multiprocessing.cpu_count() - 2)


def run_scraper(py_file, output_dir):
    scraper_name = os.path.splitext(os.path.basename(py_file))[0]
    os.makedirs(output_dir, exist_ok=True)
    start_time = time.time()
    try:
        # Optimize subprocess call for faster execution
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-O", py_file, output_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=300  # 5 minute timeout per scraper
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        execution_time = time.time() - start_time

        if stderr:
            print(f"""⚠️ Errors from {scraper_name}:
{stderr}""")

        if stdout:
            print(f"✅ {scraper_name} completed in {execution_time:.2f}s")
        else:
            print(f"⚠️ No output from {scraper_name} ({execution_time:.2f}s)")

        return {"scraper": scraper_name, "status": "success" if stdout else "no_output", "time": execution_time}

    except subprocess.TimeoutExpired:
        print(f"⏰ {scraper_name} timed out after 5 minutes")
        return {"scraper": scraper_name, "status": "timeout"}
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Scraper crashed: {scraper_name} -> {e} ({execution_time:.2f}s)")
        return {"scraper": scraper_name, "status": "failed", "error": str(e), "time": execution_time}


def run_all_scrapers_parallel():
    # Collect scraper files and their relative core subfolders
    scraper_jobs = []
    for root, _, files in os.walk(SCRAPER_ROOT):
        rel_subfolder = os.path.relpath(root, SCRAPER_ROOT)
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                out_dir = os.path.join(OUTPUT_ROOT, rel_subfolder)
                scraper_jobs.append((full_path, out_dir))

    print(f"🚀 Starting {len(scraper_jobs)} scrapers with max {MAX_WORKERS} concurrent (reserving 2 cores for system)...")
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(run_scraper, py_file, output_dir): (py_file, output_dir)
            for py_file, output_dir in scraper_jobs
        }
        for future in as_completed(futures):
            py_file, output_dir = futures[future]
            result = future.result()
            scraper_name = result.get("scraper")
            status = result.get("status")
            if status == "success":
                print(f"✅ {scraper_name} succeeded, output in {output_dir}")
            elif status == "no_output":
                print(f"⚠️ {scraper_name} produced no output.")
            elif status == "timeout":
                print(f"⏰ {scraper_name} timed out")
            else:
                print(f"❌ {scraper_name} failed with error: {result.get('error')}")

    total_time = time.time() - start_time
    print(f"🎉 All scrapers finished in {total_time:.2f} seconds")
    print(f"📊 Average time per scraper: {total_time/len(scraper_jobs):.2f}s")


if __name__ == "__main__":
    run_all_scrapers_parallel()
