import os
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, send_file, flash, jsonify, session
from werkzeug.utils import secure_filename
import tempfile
import threading
import time
import csv
from datetime import datetime
from email_name_merger import merge_by_email, read_list_from_excel, write_list_to_excel
from seprate import split_excel_by_industry
from cleaner import EmailListCleaner
from data_analysis import load_email_data, email_domain_distribution, plot_domain_distribution, basic_email_stats, plot_column
from ml_models import prepare_data, train_random_forest, predict_email_validity
from scraper import WebScraper
import joblib

# Global variables for trained model and label encoder
trained_clf = None
trained_le = None

# Path to save/load model and label encoder
models_dir = os.path.join(os.getcwd(), 'models')
os.makedirs(models_dir, exist_ok=True)
model_path = os.path.join(models_dir, 'random_forest_model.joblib')
le_path = os.path.join(models_dir, 'label_encoder.joblib')

# Load model and label encoder if they exist
if os.path.exists(model_path) and os.path.exists(le_path):
    trained_clf = joblib.load(model_path)
    trained_le = joblib.load(le_path)



import logging

def cleanup_old_files(directory, max_age_seconds=3600):  # 1 hour default
    """Delete files in the directory that are older than max_age_seconds."""
    now = time.time()
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                except OSError:
                    pass  # Ignore errors if file can't be deleted



app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'your-secret-key-change-this-in-production'

# Use a persistent downloads directory
downloads_dir = os.path.join(os.getcwd(), 'downloads')
os.makedirs(downloads_dir, exist_ok=True)
UPLOAD_FOLDER = downloads_dir
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'xlsx', 'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def require_login():
    allowed_endpoints = ['login', 'static']
    if request.endpoint not in allowed_endpoints and not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if email and (email.endswith('@reachengine.io') or email.lower().startswith('osho')):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Access denied.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/')
def root_redirect():
    return redirect(url_for('index'))

@app.route('/combiner.html')
def combiner():
    return render_template('combiner.html')

@app.route('/merger.html')
def merger():
    return render_template('merger.html')

@app.route('/splitter.html')
def splitter():
    return render_template('splitter.html')

@app.route('/cleaner.html')
def cleaner():
    return render_template('cleaner.html')

@app.route('/scraper.html')
def scraper():
    return render_template('scraper.html')

@app.route('/domain_validator.html')
def domain_validator():
    return render_template('domain_validator.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))
    files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        flash('No file selected')
        return redirect(url_for('index'))

    # Check if multiple files (for combiner)
    if len(files) > 1:
        # Combiner: multiple files
        filepaths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                filepaths.append(filepath)
            else:
                flash('Invalid file format')
                return redirect(url_for('index'))
        output_filename = 'combined_refined.xlsx'
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        try:
            combine_multiple_excels(filepaths, output_filepath)
            return redirect(url_for('download_file', filename=output_filename))
        except Exception as e:
            flash(f'Error processing files: {str(e)}')
            return redirect(url_for('index'))
    else:
        # Single file processing (other tools)
        file = files[0]
        if file.filename == '':
            flash('No file selected')
            return redirect(url_for('index'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Process the file
            output_filename = 'refined_' + filename
            output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            try:
                process_excel(filepath, output_filepath)
                return redirect(url_for('download_file', filename=output_filename))
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return redirect(url_for('index'))
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        response = send_file(filepath, as_attachment=True, download_name=filename)
        return response
    return "File not found"

def process_excel(input_file, output_file):
    # Adapted from combine_excel.py
    sheets = pd.read_excel(input_file, sheet_name=None)
    combined = pd.concat(sheets.values(), ignore_index=True)
    possible_email_cols = ['email', 'Email', 'email address', 'Email Address', 'e-mail', 'E-mail']
    email_col = None
    for col in combined.columns:
        if col.lower() in [p.lower() for p in possible_email_cols]:
            email_col = col
            break
    if email_col is None:
        raise ValueError("No email column found.")
    unique = combined.drop_duplicates(subset=email_col)
    unique.to_excel(output_file, index=False)

def combine_multiple_excels(filepaths, output_file):
    # Combine multiple Excel and CSV files and dedupe
    all_data = []
    for filepath in filepaths:
        ext = filepath.rsplit('.', 1)[1].lower()
        if ext == 'xlsx':
            sheets = pd.read_excel(filepath, sheet_name=None)
            combined = pd.concat(sheets.values(), ignore_index=True)
        elif ext == 'csv':
            combined = pd.read_csv(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        all_data.append(combined)
    if not all_data:
        raise ValueError("No data found in files.")
    full_combined = pd.concat(all_data, ignore_index=True)
    possible_email_cols = ['email', 'Email', 'email address', 'Email Address', 'e-mail', 'E-mail']
    email_col = None
    for col in full_combined.columns:
        if col.lower() in [p.lower() for p in possible_email_cols]:
            email_col = col
            break
    if email_col is None:
        raise ValueError("No email column found in any file.")
    # Trim whitespace and dedupe case-insensitively
    full_combined[email_col] = full_combined[email_col].astype(str).str.strip()
    full_combined['email_lower'] = full_combined[email_col].str.lower()
    unique = full_combined.drop_duplicates(subset='email_lower', keep='first')
    unique = unique.drop(columns=['email_lower'])
    unique.to_excel(output_file, index=False)

@app.route('/merge_names', methods=['POST'])
def merge_names():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get parameters
        source_sheet = request.form.get('source_sheet', 'Sheet1')
        target_sheet = request.form.get('target_sheet', 'Sheet2')
        output_filename = 'merged_' + filename
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        try:
            # Read sheets
            source_list = read_list_from_excel(filepath, source_sheet)
            target_list = read_list_from_excel(filepath, target_sheet)

            # Merge
            merged_list, matches = merge_by_email(source_list, target_list)

            # Write output
            success = write_list_to_excel(merged_list, output_filepath)
            if success:
                flash(f'Successfully merged {matches} records')
                return redirect(url_for('download_file', filename=output_filename))
            else:
                flash('Error writing merged file')
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
    return redirect(url_for('index'))

@app.route('/split_industry', methods=['POST'])
def split_industry():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get parameters
        industry_column = request.form.get('industry_column')
        output_format = request.form.get('output_format', 'separate_files')

        if not industry_column:
            flash('Industry column name is required')
            return redirect(url_for('index'))

        try:
            # Create output filename
            base_name = os.path.splitext(filename)[0]
            if output_format == 'single_file_multiple_sheets':
                output_filename = f'{base_name}_split_by_{industry_column}.xlsx'
                output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

                # Modify the split function to save to our temp folder instead of industry_split_output
                split_excel_by_industry(filepath, industry_column, output_format, output_filepath, verbose=False)
                flash('File split successfully into multiple sheets.')
                return redirect(url_for('download_file', filename=output_filename))
            else:
                # For separate files, create a zip archive
                import zipfile
                zip_filename = f'{base_name}_split_by_{industry_column}.zip'
                zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

                # Create a temporary directory for split files
                temp_split_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_split_{base_name}')
                os.makedirs(temp_split_dir, exist_ok=True)

                # Split files into temp directory
                split_excel_by_industry(filepath, industry_column, output_format, temp_split_dir, verbose=False)

                # Create zip file
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_split_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_split_dir)
                            zipf.write(file_path, arcname)

                # Clean up temp directory
                import shutil
                shutil.rmtree(temp_split_dir)

                flash('File split successfully into separate files (ZIP archive).')
                return redirect(url_for('download_file', filename=zip_filename))

        except Exception as e:
            flash(f'Error splitting file: {str(e)}')
    return redirect(url_for('index'))

@app.route('/clean_emails', methods=['POST'])
def clean_emails():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    # Allow CSV and Excel for cleaner
    allowed_exts = {'xlsx', 'xls', 'csv'}
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_exts:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get parameters
        email_column = request.form.get('email_column', 'email')
        advanced = request.form.get('advanced') == 'on'

        # Generate output filename
        input_path = os.path.splitext(filename)
        output_filename = f"{input_path[0]}_cleaned{input_path[1]}"
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        try:
            cleaner = EmailListCleaner()
            cleaned_df = cleaner.clean_email_list(filepath, email_column, output_filepath, advanced)
            if cleaned_df is not None:
                flash('Email list cleaned successfully')
                return redirect(url_for('download_file', filename=output_filename))
            else:
                flash('Error cleaning email list')
        except Exception as e:
            flash(f'Error cleaning emails: {str(e)}')
    else:
        flash('Invalid file format. Use CSV or Excel.')
    return redirect(url_for('index'))

@app.route('/matcher.html')
def matcher():
    return render_template('matcher.html')

@app.route('/match_emails', methods=['POST'])
def match_emails():
    source_file = request.files.get('source')
    target_files = request.files.getlist('target')

    if not source_file or not target_files:
        flash('Source file and at least one target file required')
        return redirect(url_for('matcher'))

    if source_file.filename == '' or any(f.filename == '' for f in target_files):
        flash('All files must be selected')
        return redirect(url_for('matcher'))

    # Check allowed files
    if not allowed_file(source_file.filename) or not all(allowed_file(f.filename) for f in target_files):
        flash('Invalid file format. Use .xlsx or .csv')
        return redirect(url_for('matcher'))

    try:
        # Save source
        source_filename = secure_filename(source_file.filename)
        source_path = os.path.join(app.config['UPLOAD_FOLDER'], source_filename)
        source_file.save(source_path)

        # Process source file
        if source_filename.endswith('.xlsx'):
            df_source = pd.read_excel(source_path)
        elif source_filename.endswith('.csv'):
            df_source = pd.read_csv(source_path)
        else:
            flash('Unsupported source file format')
            return redirect(url_for('matcher'))

        # Assume 'email' column exists
        if 'email' not in df_source.columns:
            flash("Source file must have an 'email' column")
            return redirect(url_for('matcher'))

        source_emails = set(df_source['email'].dropna())

        # Process each target file
        for target_file in target_files:
            target_filename = secure_filename(target_file.filename)
            target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)
            target_file.save(target_path)

            if target_filename.endswith('.xlsx'):
                df_target = pd.read_excel(target_path)
            elif target_filename.endswith('.csv'):
                df_target = pd.read_csv(target_path)
            else:
                continue  # Skip unsupported

            if 'email' not in df_target.columns:
                continue

            # Add a column named after the target file (without extension)
            col_name = os.path.splitext(target_filename)[0]
            target_emails = set(df_target['email'].dropna())
            df_source[col_name] = df_source['email'].apply(lambda x: 'yes' if x in target_emails else 'no')

        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'matched_output.xlsx')
        df_source.to_excel(output_path, index=False)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        flash(f'Error processing files: {str(e)}')
        return redirect(url_for('matcher'))

# New route for data analysis dashboard
@app.route('/analysis.html')
def analysis():
    return render_template('analysis.html')

# Route to upload file and show data analysis
@app.route('/analyze_data', methods=['POST'])
def analyze_data():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('analysis'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('analysis'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        email_column = request.form.get('email_column', 'email')
        selected_columns = request.form.getlist('selected_column')
        label_mapping_str = request.form.get('label_mapping')
        label_mapping = {}
        if label_mapping_str:
            for pair in label_mapping_str.split(','):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    label_mapping[k.strip()] = v.strip()
        try:
            df, actual_email_column = load_email_data(filepath, email_column)
            stats = basic_email_stats(df, actual_email_column)
            domain_counts = email_domain_distribution(df, actual_email_column)
            domain_plot = plot_domain_distribution(domain_counts)
            columns = df.columns.tolist()
            column_plots = []
            for col in selected_columns:
                if col in columns:
                    plot = plot_column(df, col, label_mapping)
                    column_plots.append((col, plot))
            return render_template('analysis.html', stats=stats, domain_plot=domain_plot, columns=columns, column_plots=column_plots)
        except Exception as e:
            flash(f'Error analyzing data: {str(e)}')
            return redirect(url_for('analysis'))
    else:
        flash('Invalid file format. Use CSV or Excel.')
        return redirect(url_for('analysis'))

# Route to train ML model
@app.route('/train_model', methods=['POST'])
def train_model():
    if 'train_file' not in request.files:
        flash('No training file uploaded')
        return redirect(url_for('analysis'))
    train_file = request.files['train_file']
    if train_file.filename == '':
        flash('No training file selected')
        return redirect(url_for('analysis'))
    if train_file and allowed_file(train_file.filename):
        filename = secure_filename(train_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        train_file.save(filepath)
        email_column = request.form.get('email_column_train', 'email')
        label_column = request.form.get('label_column', 'label')
        try:
            df, actual_email_column = load_email_data(filepath, email_column)
            if label_column not in df.columns:
                flash(f"Label column '{label_column}' not found in data")
                return redirect(url_for('analysis'))
            features, labels, le = prepare_data(df, actual_email_column, label_column)
            clf, report, accuracy = train_random_forest(features, labels)
            # Save model and label encoder in global variables for prediction
            global trained_clf, trained_le
            trained_clf = clf
            trained_le = le
            # Save model and label encoder to disk for persistence
            joblib.dump(clf, model_path)
            joblib.dump(le, le_path)
            # Save report to a file for download
            report_filename = 'training_report.txt'
            report_filepath = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
            with open(report_filepath, 'w') as f:
                f.write(report)
            return render_template('analysis.html', training_report=report, training_accuracy=accuracy, report_file=report_filename)
        except Exception as e:
            flash(f'Error training model: {str(e)}')
            return redirect(url_for('analysis'))
    else:
        flash('Invalid training file format. Use CSV or Excel.')
        return redirect(url_for('analysis'))

# Route to predict email validity
@app.route('/predict_emails', methods=['POST'])
def predict_emails():
    emails_input = request.form.get('emails_input', '')
    if not emails_input.strip():
        flash('No emails provided for prediction')
        return redirect(url_for('analysis'))
    emails = pd.Series([e.strip() for e in emails_input.strip().splitlines() if e.strip()])
    try:
        global trained_clf, trained_le
        if trained_clf is None or trained_le is None:
            flash('Model not trained yet. Please train the model first.')
            return redirect(url_for('analysis'))
        preds = predict_email_validity(trained_clf, trained_le, emails)
        results = "\n".join(f"{email}: {'Valid' if pred else 'Invalid'}" for email, pred in zip(emails, preds))
        return render_template('analysis.html', prediction_results=results)
    except Exception as e:
        flash(f'Error predicting emails: {str(e)}')
        return redirect(url_for('analysis'))







@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form.get('url')
    scrape_type = request.form.get('scrape_type')
    selector = request.form.get('selector')
    attribute = request.form.get('attribute')
    industry = request.form.get('industry')

    if not url and not industry:
        flash('Either URL or Industry is required.', 'error')
        return redirect(url_for('scraper'))

    try:
        scraper = WebScraper()
        if industry:  # LinkedIn people scraping by industry
            data = scraper.scrape_linkedin_people_by_industry(industry, location=request.form.get('location'))
        elif selector:  # If selector is provided, use specific scraping
            if scrape_type == 'dynamic':
                data = scraper.scrape_dynamic(url, selector, attribute)
            else:
                data = scraper.scrape_static(url, selector, attribute)
        else:  # If no selector, scrape comprehensive data
            data = scraper.scrape_comprehensive_data(url, scrape_type)

        if not data:
            flash('No data found.', 'warning')
            return redirect(url_for('scraper'))

        # Save data to Excel or CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if industry:
            filename = f'linkedin_people_{industry.replace(" ", "_")}_{timestamp}.xlsx'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # data is list of dicts for structured data
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False)
        else:
            filename = f'scraped_data_{timestamp}.csv'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # data is list of strings
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Data'])
                for item in data:
                    writer.writerow([item])

        flash(f'Scraping completed! Data saved to {filename}', 'success')
        return render_template('scraper.html', download_file=filename)

    except Exception as e:
        flash(f'Error during scraping: {str(e)}', 'error')
        return redirect(url_for('scraper'))

@app.route('/validate_domains', methods=['POST'])
def validate_domains():
    if 'file' not in request.files:
        flash('No file uploaded')
        return redirect(url_for('domain_validator'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('domain_validator'))

    # Allow both Excel and CSV files
    allowed_exts = {'xlsx', 'xls', 'csv'}
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_exts:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Load the file into a DataFrame
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(filepath)
            elif filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                flash('Unsupported file format')
                return redirect(url_for('domain_validator'))

            # Check if 'website' column exists
            if 'website' not in df.columns:
                flash("Error: 'website' column not found in the file. Please ensure your file has a column named 'website'.")
                return redirect(url_for('domain_validator'))

            # Import the domain validator function
            from domain_validator import validate_websites_from_dataframe

            # Validate domains and get DataFrames
            valid_df, invalid_df = validate_websites_from_dataframe(df, website_column='website')

            # Generate output filenames
            base_name = os.path.splitext(filename)[0]
            valid_filename = f'{base_name}_valid_domains.xlsx'
            invalid_filename = f'{base_name}_invalid_domains.xlsx'
            valid_filepath = os.path.join(app.config['UPLOAD_FOLDER'], valid_filename)
            invalid_filepath = os.path.join(app.config['UPLOAD_FOLDER'], invalid_filename)

            # Save the DataFrames to Excel files
            valid_df.to_excel(valid_filepath, index=False)
            invalid_df.to_excel(invalid_filepath, index=False)

            valid_count = len(valid_df)
            invalid_count = len(invalid_df)

            flash(f'Domain validation completed! Valid domains: {valid_count}, Invalid domains: {invalid_count}')
            return render_template('domain_validator.html', valid_file=valid_filename, invalid_file=invalid_filename)

        except Exception as e:
            flash(f'Error validating domains: {str(e)}')
            return redirect(url_for('domain_validator'))
    else:
        flash('Invalid file format. Use .xlsx, .xls, or .csv')
        return redirect(url_for('domain_validator'))

if __name__ == '__main__':
    app.run(debug=True)
