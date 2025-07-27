import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

from helper.pdf_extractor import extract_lines_from_pdf

def iou(a, b):
    xa1, ya1, xa2, ya2 = a
    xb1, yb1, xb2, yb2 = b
    x_left = max(xa1, xb1)
    y_top = max(ya1, yb1)
    x_right = min(xa2, xb2)
    y_bottom = min(ya2, yb2)
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    intersection = (x_right - x_left) * (y_bottom - y_top)
    area_a = (xa2 - xa1) * (ya2 - ya1)
    area_b = (xb2 - xb1) * (yb2 - yb1)
    return intersection / float(area_a + area_b - intersection)

def label_lines(all_lines, label_df, iou_thresh=0.3):
    y = []
    print("Assigning labels to lines based on annotation matches ...")
    prev_page = -1
    for i, line in enumerate(all_lines):
        if line['page'] != prev_page:
            print(f"  Matching lines for page {line['page']}")
            prev_page = line['page']
        label_this = 'None'
        cand_labels = label_df[label_df['page'] == line['page']]
        for _, label in cand_labels.iterrows():
            gt_box = (label['x1'], label['y1'], label['x2'], label['y2'])
            line_box = (line['x1'], line['y1'], line['x2'], line['y2'])
            if iou(line_box, gt_box) > iou_thresh:
                label_this = label['level']
                break
        y.append(label_this)
        if i < 5:
            print(f"[Sample {i+1}] '{line['text']}' assigned label: {label_this}")
    print("All lines labeled.")
    return y

def main():
    pdf_path = "train-test/1.pdf"
    label_csv = "labels.csv"

    print("Loading annotation data ...")
    label_df = pd.read_csv(label_csv)
    print(f"Total labeled heading regions: {len(label_df)}")

    all_lines = extract_lines_from_pdf(pdf_path, timeout=4)
    y = label_lines(all_lines, label_df)

    print("\nBuilding feature matrix ...")
    features = np.array([[l['font_size'], int(l['is_bold']), len(l['text'])] for l in all_lines])
    labels = np.array(y)

    print(f"Feature matrix shape: {features.shape}")
    print(f"Labels vector shape: {labels.shape}")

    print("Splitting data for training/testing ...")
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    print(f"Train set size: {X_train.shape[0]}")
    print(f"Test set size: {X_test.shape[0]}")

    print("Starting RandomForest training ...")
    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(X_train, y_train)
    print("Training complete.")

    print("Evaluating on test set:")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))

    model_path = "heading_classifier.pkl"
    joblib.dump(clf, model_path)
    print(f"Model saved as {model_path}")

if __name__ == "__main__":
    main()
