from sktime.datasets import load_arrow_head
from sktime.classification.distance_based import KNeighborsTimeSeriesClassifier
from sktime.classification.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Debug: Start of the script
print("Debug: Starting script...")

# Load the ArrowHead dataset
print("Debug: Loading ArrowHead dataset...")
X, y = load_arrow_head(return_X_y=True)
print(f"Debug: Dataset loaded. X shape: {X.shape}, y shape: {y.shape}")

# Split the data into training and testing sets
print("Debug: Splitting dataset into training and testing sets...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05, random_state=42)
print(f"Debug: Data split complete. X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")

# Initialize the kNN classifier with DTW as the distance metric
print("Debug: Initializing kNN classifier with DTW distance metric...")
knn_classifier = KNeighborsTimeSeriesClassifier(n_neighbors=1, distance="dtw")

# Train the kNN classifier
print("Debug: Training kNN classifier...")
knn_classifier.fit(X_train, y_train)
print("Debug: kNN classifier training complete.")

# Make predictions using the kNN classifier
print("Debug: Making predictions with kNN classifier...")
y_pred_knn = knn_classifier.predict(X_test)
print("Debug: kNN predictions complete.")

# Evaluate kNN classifier accuracy
accuracy_knn = accuracy_score(y_test, y_pred_knn)
print(f"Debug: kNN Classifier Accuracy: {accuracy_knn:.2f}")

# Initialize the DummyClassifier with the "most_frequent" strategy
print("Debug: Initializing DummyClassifier with 'most_frequent' strategy...")
dummy_classifier = DummyClassifier(strategy="most_frequent")

# Train the DummyClassifier
print("Debug: Training DummyClassifier...")
dummy_classifier.fit(X_train, y_train)
print("Debug: DummyClassifier training complete.")

# Make predictions using the DummyClassifier
print("Debug: Making predictions with DummyClassifier...")
y_pred_dummy = dummy_classifier.predict(X_test)
print("Debug: DummyClassifier predictions complete.")

# Evaluate DummyClassifier accuracy
accuracy_dummy = accuracy_score(y_test, y_pred_dummy)
print(f"Debug: DummyClassifier Accuracy: {accuracy_dummy:.2f}")

# Compare results
print("Debug: Comparing results...")
if accuracy_knn > accuracy_dummy:
    print("kNN Classifier outperforms DummyClassifier.")
else:
    print("DummyClassifier outperforms kNN Classifier.")

# Debug: End of the script
print("Debug: Script execution complete.")
