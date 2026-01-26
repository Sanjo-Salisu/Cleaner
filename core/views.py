import pandas as pd
import numpy as np
from django.shortcuts import render
from .forms import UploadForm
from django.conf import settings
import os


def remove_outliers_and_gaps(df):
    # Work only with numeric columns
    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.empty:
        return df, "No numeric columns found — nothing to clean."

    # ---- OUTLIER REMOVAL (IQR METHOD) ----
    Q1 = numeric_df.quantile(0.25)
    Q3 = numeric_df.quantile(0.75)
    IQR = Q3 - Q1

    mask = ~((numeric_df < (Q1 - 1.5 * IQR)) | 
             (numeric_df > (Q3 + 1.5 * IQR))).any(axis=1)

    df_clean = df.loc[mask].copy()

    # ---- WIDE SPACING (GAP) HANDLING ----
    for col in numeric_df.columns:
        sorted_vals = df_clean[col].sort_values()
        diffs = sorted_vals.diff()

        # Identify unusually large gaps
        gap_threshold = diffs.mean() + 2 * diffs.std()
        large_gaps = diffs > gap_threshold

        # Remove rows causing extreme gaps
        df_clean = df_clean[~df_clean[col].isin(sorted_vals[large_gaps].values)]

    message = (
        f"Cleaned dataset: removed outliers and extreme gaps.\n"
        f"Original rows: {len(df)} | Cleaned rows: {len(df_clean)}"
    )

    return df_clean, message


def upload_dataset(request):
    original_preview = None
    cleaned_preview = None
    message = None
    cleaned_file_path = None

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            dataset = form.save()
            file_path = dataset.file.path

            # Read file (CSV or Excel)
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            original_preview = df.head(100).to_html(classes="table")

            # Clean data
            df_clean, message = remove_outliers_and_gaps(df)

            cleaned_preview = df_clean.head(100).to_html(classes="table")

            # Save cleaned file
            cleaned_file_path = file_path.replace(".csv", "_cleaned.csv").replace(".xlsx", "_cleaned.xlsx")

            if cleaned_file_path.endswith(".csv"):
                df_clean.to_csv(cleaned_file_path, index=False)
            else:
                df_clean.to_excel(cleaned_file_path, index=False)

    else:
        form = UploadForm()

    return render(request, "upload.html", {
        "form": form,
        "original_preview": original_preview,
        "cleaned_preview": cleaned_preview,
        "message": message,
        "cleaned_file_path": cleaned_file_path
    })

