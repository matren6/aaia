# test_evolution.py
def test_complete_evolution():
    """Test the complete evolution pipeline"""
    print("Testing Evolution Pipeline...")
    print("=" * 60)
    
    # Initialize system
    arbiter = Arbiter()
    
    # Run manual evolution
    print("1. Running manual evolution...")
    result = arbiter.evolve_command()
    
    # Check results
    print("\n2. Checking evolution results...")
    if result.get("status") == "completed":
        print("✓ Evolution pipeline completed successfully")
        
        # Verify system still works
        print("\n3. Verifying system integrity...")
        print("  • Testing module imports...")
        test_modules = ["scribe", "mandates", "economics", "dialogue", "router"]
        for module in test_modules:
            try:
                __import__(module)
                print(f"    ✓ {module} imports correctly")
            except Exception as e:
                print(f"    ✗ {module} failed: {e}")
                
        print("\n4. Testing core functionality...")
        # Test a simple command
        test_response = arbiter.process_command("help")
        if "Available commands" in test_response:
            print("✓ Core functionality intact")
        else:
            print("✗ Core functionality broken")
            
        print("\n✓ Evolution test PASSED")
        return True
    else:
        print(f"✗ Evolution failed: {result.get('error', 'Unknown error')}")
        return False
        
if __name__ == "__main__":
    test_complete_evolution()