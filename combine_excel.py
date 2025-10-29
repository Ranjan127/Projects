import pandas as pd
import sys

if len(sys.argv) != 3:
    print("Usage: python combine_excel.py <input_file.xlsx> <output_file.xlsx>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Read all sheets from the Excel file
sheets = pd.read_excel(input_file, sheet_name=None)

# Combine all sheets into a single DataFrame
combined = pd.concat(sheets.values(), ignore_index=True)

# Possible email column names (case insensitive)
possible_email_cols = ['email', 'Email', 'email address', 'Email Address', 'e-mail', 'E-mail']

# Find the email column
email_col = None
for col in combined.columns:
    if col.lower() in [p.lower() for p in possible_email_cols]:
        email_col = col
        break

if email_col is None:
    print("Error: No email column found. Possible names: email, Email, email address, etc.")
    sys.exit(1)

# Drop duplicates based on the email column, keeping the first occurrence
unique = combined.drop_duplicates(subset=email_col)

# Save the unique rows to a new Excel file
unique.to_excel(output_file, index=False)

print(f"Unique rows saved to {output_file} based on '{email_col}' column")
