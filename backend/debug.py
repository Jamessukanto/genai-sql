#!/usr/bin/env python3
print("Debug script starting...")

try:
    import setup_and_run
    print("Import successful")
    
    print("About to call main()")
    setup_and_run.main()
    print("Main completed successfully")
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
    print("Debug script finished with error")
else:
    print("Debug script finished successfully") 