import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def prepare_data(df, email_column='email', label_column='label'):
    """
    Prepare data for ML model.
    label_column: column with target labels (e.g., valid/invalid)
    """
    # Simple feature: length of email, domain encoded
    df = df.copy()
    df['email_length'] = df[email_column].astype(str).apply(len)
    df['domain'] = df[email_column].str.split('@').str[1].fillna('unknown')
    le = LabelEncoder()
    df['domain_encoded'] = le.fit_transform(df['domain'])
    features = df[['email_length', 'domain_encoded']]
    labels = df[label_column]
    return features, labels, le

def train_random_forest(features, labels):
    """Train a Random Forest classifier."""
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    return clf, report, accuracy

def predict_email_validity(clf, le, emails):
    """
    Predict validity of emails using trained classifier.
    emails: list or pd.Series of email strings
    """
    import numpy as np
    email_length = emails.astype(str).apply(len)
    domains = emails.str.split('@').str[1].fillna('unknown')
    domain_encoded = le.transform(domains)
    features = pd.DataFrame({'email_length': email_length, 'domain_encoded': domain_encoded})
    preds = clf.predict(features)
    return preds
