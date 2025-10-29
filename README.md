# Email Tools Website

A comprehensive Flask web application that provides multiple email processing tools in one convenient interface.

## Features

### 🧹 Email Tools Available

1. **Excel Combiner & Deduper**
   - Combines multiple Excel sheets into one
   - Removes duplicate emails automatically
   - Perfect for consolidating contact lists

2. **Email Name Merger**
   - Merges first names from source sheets to target sheets
   - Matches records by email address
   - Enriches contact data from multiple sources

3. **Industry Splitter**
   - Splits Excel files by industry or any category column
   - Creates separate files or sheets for each category
   - Ideal for targeted marketing campaigns

4. **Email Cleaner**
   - Removes duplicates, invalid formats, and problematic emails
   - Filters out disposable and role-based email addresses
   - Optional DNS validation for thorough cleaning

5. **Data Analysis Dashboard**
   - Analyze email data with statistics and visualizations
   - Domain distribution charts
   - Duplicate analysis and data quality metrics
   - Powered by pandas, matplotlib, and seaborn

6. **Email Verifier**
   - Bulk authenticate email domains using SPF, DKIM, and DMARC protocols
   - Verify the legitimacy of your email lists with comprehensive security checks
   - Check sender policy framework (SPF) records
   - Validate domain keys identified mail (DKIM) signatures
   - Verify domain-based message authentication (DMARC) policies
   - Get authentication scores for each email domain

## Local Development

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd email-tools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and visit `http://localhost:5000`

## Vercel Deployment

### Prerequisites
- Vercel account
- Vercel CLI (optional, can deploy via GitHub integration)

### Deploy to Vercel

#### Option 1: Using Vercel CLI
1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy:
```bash
vercel
```

3. Follow the prompts to configure your deployment

#### Option 2: GitHub Integration
1. Push your code to a GitHub repository
2. Connect your repository to Vercel
3. Vercel will automatically detect the `vercel.json` configuration and deploy

### Vercel Configuration

The application is configured for Vercel with:
- Serverless function entry point at `api/index.py`
- All routes handled by the Flask app
- Temporary file storage in `/tmp` for serverless environment

## File Structure

```
email-tools/
├── api/
│   └── index.py          # Vercel serverless entry point
├── templates/
│   ├── index.html        # Main web interface
│   ├── verifier.html     # Email verifier UI
│   └── analysis.html     # Data analysis dashboard
├── app.py                # Flask application
├── vercel.json          # Vercel deployment configuration
├── requirements.txt     # Python dependencies
├── email_name_merger.py # Name merging tool
├── seprate.py          # Industry splitter tool
├── cleaner.py          # Email cleaning tool
├── email_auth.py       # Email authentication module
├── data_analysis.py    # Data analysis functions
├── ml_models.py        # Machine learning models
└── README.md           # This file
```

## Data Science & Machine Learning Libraries

This project includes a comprehensive set of Python libraries for data manipulation, analysis, visualization, and machine learning, enabling advanced processing and insights from email data:

### 1. Data Manipulation & Analysis
- **Pandas** → For data cleaning, exploration, and manipulation (reading CSVs, filtering data, grouping, merging tables)
- **NumPy** → For numerical computation and arrays (fast matrix operations and statistics)

### 2. Data Visualization
- **Matplotlib** → Basic plotting (line, bar, scatter, histograms)
- **Seaborn** → High-level statistical plots (heatmaps, pairplots, etc.)
- **Plotly** → Interactive dashboards and web-based visuals

### 3. Machine Learning
- **Scikit-learn (sklearn)** → Regression, classification, clustering, model evaluation
- **XGBoost / LightGBM / CatBoost** → Advanced boosting models
- **TensorFlow / PyTorch** → Deep learning frameworks

### 4. Data Preprocessing & Automation
- **Regex (re)** → Cleaning messy text data
- **datetime** → Handling date/time data
- **os / glob** → File automation (reading multiple files)

### 5. Statistics & Math
- **SciPy** → Statistical tests and distributions
- **Statsmodels** → Regression analysis, ANOVA, time series models

## Usage

1. Visit the deployed website or run locally
2. Choose the tool that fits your needs
3. Upload your Excel/CSV file
4. Configure any required parameters
5. Click process and download your results

## Limitations on Vercel

- File size limits (typically 5MB for uploads)
- Processing time limits (10 seconds for hobby plan)
- No persistent file storage (files are temporary)
- DNS validation may be slower due to serverless cold starts

For large files or heavy processing, consider running locally or using a VPS deployment.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.
