import pandas as pd
import sys

if len(sys.argv) != 3:
    print("Usage: python compare_sheets.py <source_file> <target_file>")
    sys.exit(1)

source_file = sys.argv[1]
target_file = sys.argv[2]

# Load the source file
if source_file.endswith('.xlsx'):
    df_source = pd.read_excel(source_file)
elif source_file.endswith('.csv'):
    df_source = pd.read_csv(source_file)
else:
    print("Unsupported source file format")
    sys.exit(1)

# Load the target file
if target_file.endswith('.xlsx'):
    df_target = pd.read_excel(target_file)
elif target_file.endswith('.csv'):
    df_target = pd.read_csv(target_file)
else:
    print("Unsupported target file format")
    sys.exit(1)

# Assume 'email' column exists in source
source_emails = set(df_source['email'].dropna())

# Add columns to df_source for each column in df_target except 'email'
for col in df_target.columns:
    if col != 'email':
        target_values = set(df_target[col].dropna())
        df_source[col] = df_source['email'].apply(lambda x: 'yes' if x in target_values else 'no')

# Write the updated DataFrame to a new Excel file
df_source.to_excel('output.xlsx', index=False)
print("Output saved to output.xlsx")
