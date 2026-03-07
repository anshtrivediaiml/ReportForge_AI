"""
Test script to verify new endpoints are properly configured
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    
    try:
        from app.schemas.reports import UserStatsResponse, JobTitleUpdate, DeleteResponse
        print("[OK] reports schemas imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import reports schemas: {e}")
        return False
    
    try:
        from app.routers import reports
        print("[OK] reports router imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import reports router: {e}")
        return False
    
    try:
        from app.routers.jobs import router as jobs_router
        print("[OK] jobs router imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import jobs router: {e}")
        return False
    
    try:
        from app.services.job_service import get_job, list_jobs, update_job, delete_job
        print("[OK] job service functions imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import job service: {e}")
        return False
    
    return True

def test_route_definitions():
    """Test that routes are properly defined"""
    print("\nTesting route definitions...")
    
    try:
        from app.routers import reports
        from app.routers import jobs
        
        # Check reports routes
        reports_routes = [r for r in reports.router.routes if hasattr(r, 'path')]
        print(f"[OK] Reports router has {len(reports_routes)} route(s)")
        
        # Check jobs routes
        jobs_routes = [r for r in jobs.router.routes if hasattr(r, 'path')]
        print(f"[OK] Jobs router has {len(jobs_routes)} route(s)")
        
        # List all routes
        print("\nReports routes:")
        for route in reports_routes:
            methods = getattr(route, 'methods', set())
            path = getattr(route, 'path', 'unknown')
            print(f"   {', '.join(methods)} {path}")
        
        print("\nJobs routes:")
        for route in jobs_routes:
            methods = getattr(route, 'methods', set())
            path = getattr(route, 'path', 'unknown')
            print(f"   {', '.join(methods)} {path}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to check routes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schemas():
    """Test that schemas are properly defined"""
    print("\nTesting schemas...")
    
    try:
        from app.schemas.reports import UserStatsResponse, JobTitleUpdate, DeleteResponse
        
        # Test JobTitleUpdate
        update = JobTitleUpdate(title="Test Report")
        assert update.title == "Test Report"
        print("[OK] JobTitleUpdate schema works")
        
        # Test DeleteResponse
        delete_resp = DeleteResponse(success=True, message="Deleted", job_id="123")
        assert delete_resp.success == True
        print("[OK] DeleteResponse schema works")
        
        return True
    except Exception as e:
        print(f"[ERROR] Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing New Endpoints Configuration")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_schemas()
    all_passed &= test_route_definitions()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed! Endpoints are properly configured.")
    else:
        print("[FAILED] Some tests failed. Please check the errors above.")
    print("=" * 60)

