import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor
import joblib

# Load data
df = pd.read_csv("telemetry_data.csv")

# Derive new control columns
df["steer"] = df["steer_left"] - df["steer_right"]
df["accel"] = df["accelerate"]

# Define columns
feature_cols = [
    "angle", "curLapTime", "distFromStart", "distRaced", "fuel", "gear",
    "lastLapTime", "racePos", "rpm", "speedX", "speedY", "speedZ",
    "trackPos", "z"
] + [f"track_{i}" for i in range(19)]

target_regression = ["accel", "brake", "steer"]
target_classification = "gear"

used_cols = feature_cols + target_regression + [target_classification]
df_clean = df[used_cols].replace("None", np.nan).dropna()

# ✅ Vectorized cleaning: strip brackets & take first value
def clean_column(col):
    return (
        col.astype(str)
        .str.replace('[', '', regex=False)
        .str.replace(']', '', regex=False)
        .str.split()
        .str[0]
        .astype(float)
    )

df_clean = df_clean.apply(clean_column)

# Final cleanup
df_clean = df_clean.dropna()

# Split data
X = df_clean[feature_cols]
y_reg = df_clean[target_regression]
y_clf = df_clean[target_classification].astype(int)

# Train/test split
X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
    X, y_reg, y_clf, test_size=0.2, random_state=42
)

# Train models
reg_model = MultiOutputRegressor(RandomForestRegressor(n_estimators=20, random_state=42))
reg_model.fit(X_train, y_reg_train)

clf_model = RandomForestClassifier(n_estimators=20, random_state=42)
clf_model.fit(X_train, y_clf_train)

# Save
joblib.dump(reg_model, "torcs_reg_model.pkl")
joblib.dump(clf_model, "torcs_gear_classifier.pkl")

print("✅ Training completed! Models saved.")
