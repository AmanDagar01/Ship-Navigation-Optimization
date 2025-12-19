import pandas as pd
import numpy as np
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import joblib

class ShipFrequencyPredictor:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = None
        self.feature_importance_ = None
        self.pipeline = None
        self.feature_columns = [
            'Longitude', 'Latitude',
            'U_Current', 'V_Current',
            'temperature_2m_min', 'temperature_2m_max',
            'pressure_msl', 'wind_direction_10m_dominant',
            'precipitation_probability_max', 'TP'
        ]

    def load_data(self, file_path="merged_data_with_ship_frequency.csv"):
        df = pd.read_csv(file_path)
        if 'ship_frequency' not in df.columns:
            raise ValueError("ship_frequency column not found in the data!")
        for col in self.feature_columns:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")
        X = df[self.feature_columns]
        y = df['ship_frequency']
        return X, y, df

    def split_data(self, X, y, df, test_size=0.33):
        # Stratify by date if available, else random split
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            # Use the last N days as test set
            unique_dates = np.sort(df['Date'].unique())
            split_idx = int(len(unique_dates) * (1 - test_size))
            train_dates = unique_dates[:split_idx]
            test_dates = unique_dates[split_idx:]
            train_mask = df['Date'].isin(train_dates)
            test_mask = df['Date'].isin(test_dates)
            return X[train_mask], X[test_mask], y[train_mask], y[test_mask]
        else:
            return train_test_split(X, y, test_size=test_size, random_state=self.random_state)

    def train(self, X_train, y_train):
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=self.random_state,
                n_jobs=-1
            ))
        ])
        self.pipeline.fit(X_train, y_train)
        self.model = self.pipeline.named_steps['rf']
        self.feature_importance_ = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

    def evaluate(self, X_test, y_test):
        y_pred = self.pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        metrics = {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R2_Score': r2
        }
        return metrics, y_pred

    def save(self, model_path="ship_frequency_model.pkl"):
        joblib.dump(self.pipeline, model_path)
        # self.feature_importance_.to_csv("feature_importance.csv", index=False) # Removed as per edit

    def predict(self, param_dict):
        # param_dict: dict of feature_name: value
        X_new = pd.DataFrame([param_dict])[self.feature_columns]
        return self.pipeline.predict(X_new)[0]

    def run(self, file_path="merged_data_with_ship_frequency.csv"):
        X, y, df = self.load_data(file_path)
        # Split by date, but keep the last day for heuristic evaluation
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            unique_dates = np.sort(df['Date'].unique())
            # Use all but the last day for train/test, last day for heuristic
            train_test_dates = unique_dates[:-1]
            heuristic_date = unique_dates[-1]
            train_test_mask = df['Date'].isin(train_test_dates)
            heuristic_mask = df['Date'] == heuristic_date
            X_train_test = X[train_test_mask]
            y_train_test = y[train_test_mask]
            X_heuristic = X[heuristic_mask]
            y_heuristic = y[heuristic_mask]
            # Standard train/test split on train_test set
            X_train, X_test, y_train, y_test = train_test_split(
                X_train_test, y_train_test, test_size=0.33, random_state=self.random_state)
        else:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=self.random_state)
            X_heuristic, y_heuristic = None, None
        self.train(X_train, y_train)
        metrics, y_pred = self.evaluate(X_test, y_test)
        self.save()  # Only saves model, not feature importance
        print("Metrics:", metrics)
        # If heuristic day exists, evaluate and save heuristic score
        if X_heuristic is not None:
            heuristic_pred = self.pipeline.predict(X_heuristic)
            # Normalize to [0,1] for heuristic score
            min_pred = heuristic_pred.min()
            max_pred = heuristic_pred.max()
            if max_pred > min_pred:
                heuristic_score = (heuristic_pred - min_pred) / (max_pred - min_pred)
            else:
                heuristic_score = np.zeros_like(heuristic_pred)
            
            # Get the original data for the heuristic day to extract coordinates
            df_heuristic = df[heuristic_mask]
            
            # Create dictionary with coordinates as keys and heuristic scores as values
            heuristic_dict = {}
            for idx, (_, row) in enumerate(df_heuristic.iterrows()):
                coord = (row['Longitude'], row['Latitude'])
                heuristic_dict[coord] = float(heuristic_score[idx])
            
            # Save to pickle file in the format expected by heuristicRetriever
            import pickle
            with open("heuristics_data.pkl", "wb") as f:
                pickle.dump(heuristic_dict, f)
            
            # Also save to CSV format for other uses
            results_df = pd.DataFrame({
                'Longitude': df_heuristic['Longitude'],
                'Latitude': df_heuristic['Latitude'],
                'actual': y_heuristic,
                'predicted': heuristic_pred,
                'heuristic_score': heuristic_score
            })
            results_df.to_csv("heuristics_data.csv", index=False)
            
            print(f"Heuristic scores for last day saved to heuristics_data.pkl and heuristics_data.csv")
        return metrics

if __name__ == "__main__":
    predictor = ShipFrequencyPredictor(random_state=42)
    predictor.run()
    # Example for later use:
    # params = { ... }  # dict with all required features
    # print(predictor.predict(params))