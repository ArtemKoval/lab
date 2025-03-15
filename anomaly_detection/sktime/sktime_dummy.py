# Step 1: Install sktime (if not already installed)
# Run this command in your terminal or notebook:
# !pip install sktime

# Step 2: Import necessary libraries
from sktime.datasets import load_arrow_head
from sktime.classification.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Step 3: Load the dataset and split into train/test sets
X, y = load_arrow_head(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Step 4: Initialize and fit the DummyClassifier
# Using the "most_frequent" strategy
dummy_clf = DummyClassifier(strategy="most_frequent")
dummy_clf.fit(X_train, y_train)

# Step 5: Make predictions and evaluate performance
y_pred = dummy_clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy of DummyClassifier (most_frequent): {accuracy:.2f}")

# Step 6: Experiment with the "stratified" strategy
dummy_clf_stratified = DummyClassifier(strategy="stratified")
dummy_clf_stratified.fit(X_train, y_train)
y_pred_stratified = dummy_clf_stratified.predict(X_test)
accuracy_stratified = accuracy_score(y_test, y_pred_stratified)
print(f"Accuracy of DummyClassifier (stratified): {accuracy_stratified:.2f}")