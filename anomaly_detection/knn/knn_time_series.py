import time
from sktime.datasets import load_arrow_head
from sktime.classification.distance_based import KNeighborsTimeSeriesClassifier
from sktime.classification.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Function to print elapsed time
def print_elapsed_time(start_time, message):
    elapsed_time = time.time() - start_time
    print(f"Debug: {message} [Time: {elapsed_time:.2f} seconds]")

# Debug: Start of the script
print("Debug: Starting script...")
script_start_time = time.time()

# Load the ArrowHead dataset
print("Debug: Loading ArrowHead dataset...")
load_start_time = time.time()
X, y = load_arrow_head(return_X_y=True)
print_elapsed_time(load_start_time, f"Dataset loaded. X shape: {X.shape}, y shape: {y.shape}")

# Split the data into training and testing sets
print("Debug: Splitting dataset into training and testing sets...")
split_start_time = time.time()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
print_elapsed_time(split_start_time, f"Data split complete. X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")

# Initialize the kNN classifier with DTW as the distance metric
print("Debug: Initializing kNN classifier with DTW distance metric...")
knn_init_start_time = time.time()
knn_classifier = KNeighborsTimeSeriesClassifier(n_neighbors=1, distance="dtw")
print_elapsed_time(knn_init_start_time, "kNN classifier initialized.")

# Train the kNN classifier
print("Debug: Training kNN classifier...")
knn_train_start_time = time.time()
knn_classifier.fit(X_train, y_train)
print_elapsed_time(knn_train_start_time, "kNN classifier training complete.")

# Make predictions using the kNN classifier
print("Debug: Making predictions with kNN classifier...")
knn_predict_start_time = time.time()
y_pred_knn = knn_classifier.predict(X_test)
print_elapsed_time(knn_predict_start_time, "kNN predictions complete.")

# Evaluate kNN classifier accuracy
accuracy_knn = accuracy_score(y_test, y_pred_knn)
print(f"Debug: kNN Classifier Accuracy: {accuracy_knn:.2f}")

# Initialize the DummyClassifier with the "most_frequent" strategy
print("Debug: Initializing DummyClassifier with 'most_frequent' strategy...")
dummy_init_start_time = time.time()
dummy_classifier = DummyClassifier(strategy="most_frequent")
print_elapsed_time(dummy_init_start_time, "DummyClassifier initialized.")

# Train the DummyClassifier
print("Debug: Training DummyClassifier...")
dummy_train_start_time = time.time()
dummy_classifier.fit(X_train, y_train)
print_elapsed_time(dummy_train_start_time, "DummyClassifier training complete.")

# Make predictions using the DummyClassifier
print("Debug: Making predictions with DummyClassifier...")
dummy_predict_start_time = time.time()
y_pred_dummy = dummy_classifier.predict(X_test)
print_elapsed_time(dummy_predict_start_time, "DummyClassifier predictions complete.")

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
print_elapsed_time(script_start_time, "Script execution complete.")