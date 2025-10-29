import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

def load_email_data(file_path, email_column='email'):
    """Load email data from CSV or Excel file."""
    ext = file_path.split('.')[-1].lower()
    if ext in ['csv']:
        df = pd.read_csv(file_path)
    elif ext in ['xlsx', 'xls']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")
    if email_column not in df.columns:
        # Check case insensitive match
        matching_columns = [col for col in df.columns if col.lower() == email_column.lower()]
        if matching_columns:
            email_column = matching_columns[0]
        else:
            # Auto-detect common email column names
            possible_email_cols = ['email', 'Email', 'EMAIL', 'email address', 'Email Address', 'EMAIL ADDRESS', 'e-mail', 'E-mail', 'E-MAIL']
            for col in df.columns:
                if col.lower() in [p.lower() for p in possible_email_cols]:
                    email_column = col
                    break
            else:
                raise ValueError(f"Email column '{email_column}' not found in data. Available columns: {list(df.columns)}")
    return df, email_column

def email_domain_distribution(df, email_column='email'):
    """Return a DataFrame with counts of email domains."""
    df['domain'] = df[email_column].str.split('@').str[1].str.lower()
    domain_counts = df['domain'].value_counts().reset_index()
    domain_counts.columns = ['domain', 'count']
    return domain_counts

def plot_domain_distribution(domain_counts, top_n=10):
    """Generate a bar plot for top N email domains and return as base64 PNG."""
    top_domains = domain_counts.head(top_n)
    plt.figure(figsize=(10,6))
    sns.barplot(x='count', y='domain', data=top_domains)
    plt.title(f'Top {top_n} Email Domains')
    plt.xlabel('Count')
    plt.ylabel('Domain')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

def basic_email_stats(df, email_column='email'):
    """Calculate basic statistics about the email list."""
    total_emails = len(df)
    unique_emails = df[email_column].nunique()
    duplicates = total_emails - unique_emails
    stats = {
        'total_emails': total_emails,
        'unique_emails': unique_emails,
        'duplicates': duplicates
    }
    return stats

def plot_column(df, column_name, label_mapping=None):
    """Generate a chart for the selected column and return as base64 PNG."""
    if column_name not in df.columns:
        return None
    plt.figure(figsize=(10,6))
    if df[column_name].dtype == 'object' or df[column_name].dtype.name == 'category':
        # Categorical: pie chart
        if label_mapping:
            value_counts = df[column_name].map(label_mapping).fillna(df[column_name]).value_counts().head(10)
        else:
            value_counts = df[column_name].value_counts().head(10)  # Top 10
        plt.pie(value_counts, labels=value_counts.index, autopct='%1.1f%%', startangle=140)
        plt.title(f'Pie Chart for {column_name}')
    else:
        # Numerical: bar chart (histogram)
        plt.hist(df[column_name].dropna(), bins=20, edgecolor='black')
        plt.title(f'Histogram for {column_name}')
        plt.xlabel(column_name)
        plt.ylabel('Frequency')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64
