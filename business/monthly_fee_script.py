# SMS/business/monthly_fee_script.py
# Acts as the original script, calling the new service layer function.
import os
import sys
# Add parent directory to path for running directly from the terminal
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from business.due_service import add_monthly_fees_for_all_students

# This allows you to run the file directly
if __name__ == "__main__":
    add_monthly_fees_for_all_students()