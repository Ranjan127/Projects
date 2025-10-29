#!/usr/bin/env python3
"""
Email Sheet Merger Script

This script compares two sheets in an Excel file and merges  emails from the source sheet
to the target sheet where emails match, then creates a new Excel file with the merged data.

Usage:
    python email_name_merger.py
"""

import csv
import json
import pandas as pd
from typing import List, Dict, Tuple

def read_list_from_csv(filename: str) -> List[Dict[str, str]]:
    """Read a list of contacts from CSV file."""
    contacts = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                contacts.append(dict(row))
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file '{filename}': {str(e)}")
        return []
    return contacts

def read_list_from_json(filename: str) -> List[Dict[str, str]]:
    """Read a list of contacts from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{filename}'.")
        return []
    except Exception as e:
        print(f"Error reading file '{filename}': {str(e)}")
        return []

def read_list_from_excel(filename: str, sheet_name: str = 0) -> List[Dict[str, str]]:
    """Read a list of contacts from Excel file (.xlsx, .xls)."""
    try:
        df = pd.read_excel(filename, sheet_name=sheet_name)
        return df.to_dict('records')
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"Error reading Excel file '{filename}': {str(e)}")
        return []

def merge_by_email(
    source_list: List[Dict[str, str]],
    target_list: List[Dict[str, str]],
    email_key: str = ['email','Email']
) -> Tuple[List[Dict[str, str]], int]:
    """
    Compare source and target lists based on matching emails and create a new list
    with all columns and rows that got matched.
    
    Args:
        source_list: List of dictionaries containing source data
        target_list: List of dictionaries containing target data
        email_key: Key name for email field in dictionaries
    
    Returns:
        Tuple of (matched list with combined data, number of matches found)
    """
    updated_count = 0
    
    # Create email to source data mapping
    email_to_data = {}
    for contact in source_list:
        email = contact.get(email_key, '').lower().strip()
        if email:
            email_to_data[email] = contact
    
    # Create list of matched rows with combined data
    matched_list = []
    for contact in target_list:
        email = contact.get(email_key, '').lower().strip()
        
        if email in email_to_data:
            # Combine data from source and target
            combined = {**email_to_data[email], **contact}
            matched_list.append(combined)
            updated_count += 1
    
    return matched_list, updated_count

def write_list_to_csv(contacts: List[Dict[str, str]], filename: str) -> bool:
    """Write list of contacts to CSV file."""
    if not contacts:
        print("Warning: No contacts to write.")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=contacts[0].keys())
            writer.writeheader()
            writer.writerows(contacts)
        return True
    except Exception as e:
        print(f"Error writing to file '{filename}': {str(e)}")
        return False

def write_list_to_json(contacts: List[Dict[str, str]], filename: str) -> bool:
    """Write list of contacts to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(contacts, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing to file '{filename}': {str(e)}")
        return False

def write_list_to_excel(contacts: List[Dict[str, str]], filename: str, sheet_name: str = 'Sheet1') -> bool:
    """Write list of contacts to Excel file."""
    if not contacts:
        print("Warning: No contacts to write.")
        return False

    try:
        df = pd.DataFrame(contacts)
        df.to_excel(filename, sheet_name=sheet_name, index=False)
        return True
    except Exception as e:
        print(f"Error writing to file '{filename}': {str(e)}")
        return False

def create_sample_files():
    """Create sample CSV files for testing."""
    # Sample source list with emails and first names
    source_data = [
        {'email': 'john.doe@example.com', 'first_name': 'John', 'last_name': 'Doe'},
        {'email': 'jane.smith@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
        {'email': 'bob.johnson@example.com', 'first_name': 'Bob', 'last_name': 'Johnson'},
        {'email': 'alice.wilson@example.com', 'first_name': 'Alice', 'last_name': 'Wilson'}
    ]
    
    # Sample target list with emails but missing first names
    target_data = [
        {'email': 'john.doe@example.com', 'last_name': 'Doe', 'phone': '555-0101'},
        {'email': 'jane.smith@example.com', 'last_name': 'Smith', 'phone': '555-0102'},
        {'email': 'charlie.brown@example.com', 'last_name': 'Brown', 'phone': '555-0103'},
        {'email': 'bob.johnson@example.com', 'last_name': 'Johnson', 'phone': '555-0104'}
    ]
    
    # Write sample files
    write_list_to_csv(source_data, 'source_list.csv')
    write_list_to_csv(target_data, 'target_list.csv')
    
    print("Sample files created: source_list.csv and target_list.csv")

def main():
    """Main function to run the email sheet merger."""
    print("Email Sheet Merger Script")
    print("=" * 30)

    # Ask user if they want to create sample files
    choice = input("Create sample files for testing? (y/n): ").lower().strip()
    if choice == 'y':
        create_sample_files()
        return

    # Get Excel file name
    excel_file = input("Enter Excel file name: ").strip()
    if not excel_file:
        excel_file = 'newjonny.xlsx'

    # List sheets
    try:
        xl = pd.ExcelFile(excel_file)
        sheets = xl.sheet_names
        print(f"Available sheets: {sheets}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Get sheet names
    source_sheet = input("Enter source sheet name: ").strip()
    if not source_sheet:
        source_sheet = sheets[0] if sheets else 'Sheet1'

    target_sheet = input("Enter target sheet name: ").strip()
    if not target_sheet:
        target_sheet = sheets[1] if len(sheets) > 1 else 'Sheet2'

    output_file = input("Enter output Excel file name: ").strip()
    if not output_file:
        output_file = 'merged.xlsx'
    if not output_file.endswith('.xlsx'):
        output_file += '.xlsx'

    # Read sheets
    source_list = read_list_from_excel(excel_file, source_sheet)
    target_list = read_list_from_excel(excel_file, target_sheet)

    if not source_list or not target_list:
        print("Error: Unable to read sheets.")
        return

    # Merge data
    updated_list, matches = merge_by_email(source_list, target_list)

    print(f"\nProcessing complete:")
    print(f"- Source sheet: {len(source_list)} contacts")
    print(f"- Target sheet: {len(target_list)} contacts")
    print(f"- Matches found: {matches}")

    # Write output to Excel
    success = write_list_to_excel(updated_list, output_file)

    if success:
        print(f"- Updated list written to: {output_file}")
    else:
        print("Error: Failed to write output file.")

if __name__ == "__main__":
    main()
