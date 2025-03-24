# Z-Score Anomaly Detection on UCI Iris Dataset

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.metrics import roc_curve, auc, classification_report
from sklearn.model_selection import train_test_split
from scipy import stats

# Set random seed for reproducibility
np.random.seed(42)

# 1. Load and prepare the Iris dataset from UCI
print("Loading Iris dataset from UCI repository...")
iris = load_iris()
df = pd.DataFrame(data=np.c_[iris['data'], iris['target']],
                  columns=iris['feature_names'] + ['target'])

# For anomaly detection, we'll treat Iris-setosa (target=0) as normal
# and the other species as anomalies (target=1)
df['label'] = df['target'].apply(lambda x: 0 if x == 0 else 1)

# We'll use sepal length as our feature for this demo
feature_col = 'sepal length (cm)'
X = df[[feature_col]].values
y = df['label'].values

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y)

# Use only normal data (setosa) for training
X_train_normal = X_train[y_train == 0]

print("\nClass distribution in test set:")
print(pd.Series(y_test).value_counts())
print(f"Anomaly rate: {y_test.mean() * 100:.2f}%")


# 2. Implement Z-Score Anomaly Detector
class ZScoreAnomalyDetector:
    def __init__(self, threshold=2.5):
        self.threshold = threshold
        self.mean = None
        self.std = None

    def fit(self, X):
        """Learn the mean and std of normal data"""
        self.mean = np.mean(X)
        self.std = np.std(X)
        if self.std == 0:
            self.std = 1e-10  # Avoid division by zero

    def predict(self, X):
        """Predict anomalies (binary)"""
        z_scores = np.abs((X - self.mean) / self.std)
        return (z_scores > self.threshold).astype(int)

    def predict_proba(self, X):
        """Predict anomaly probabilities"""
        z_scores = np.abs((X - self.mean) / self.std)
        # Convert z-scores to probabilities using survival function
        return 2 * stats.norm.sf(z_scores)


# 3. Train and evaluate the detector
print("\nTraining z-score anomaly detector...")
detector = ZScoreAnomalyDetector(threshold=2.5)
detector.fit(X_train_normal)

# Make predictions
y_pred = detector.predict(X_test)
y_scores = detector.predict_proba(X_test).ravel()

# 4. Evaluate performance
print("\nEvaluation Metrics:")
print(classification_report(y_test, y_pred, target_names=['Setosa', 'Non-Setosa']))

# Calculate ROC curve
fpr, tpr, thresholds = roc_curve(y_test, y_scores)
roc_auc = auc(fpr, tpr)

# Find optimal threshold (Youden's J statistic)
J = tpr - fpr
ix = np.argmax(J)
best_thresh = thresholds[ix]

print(f"\nOptimal threshold: {best_thresh:.4f} (Youden's J = {J[ix]:.2f})")

# Apply optimal threshold
optimized_pred = (y_scores >= (2 * stats.norm.sf(best_thresh))).astype(int)
print("\nOptimized Performance:")
print(classification_report(y_test, optimized_pred, target_names=['Setosa', 'Non-Setosa']))

# 5. Plot results
plt.figure(figsize=(12, 5))

# ROC Curve
plt.subplot(1, 2, 1)
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.scatter(fpr[ix], tpr[ix], marker='o', color='black', label=f'Optimal threshold')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")

# Feature distribution with threshold
plt.subplot(1, 2, 2)
plt.hist(X_test[y_test == 0], bins=15, alpha=0.5, label='Setosa (Normal)')
plt.hist(X_test[y_test == 1], bins=15, alpha=0.5, label='Non-Setosa (Anomaly)')
plt.axvline(x=detector.mean + detector.threshold * detector.std,
            color='red', linestyle='--', label=f'Threshold (z={detector.threshold})')
plt.xlabel('Sepal Length (cm)')
plt.ylabel('Frequency')
plt.title('Distribution of Sepal Length by Class')
plt.legend()

plt.tight_layout()
plt.show()

print("\nAnalysis complete!")