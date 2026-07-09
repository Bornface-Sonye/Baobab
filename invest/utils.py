import string
import random



#Machine Learning imports;
import os
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from django.conf import settings

import os
import joblib
import numpy as np
import pandas as pd

from django.conf import settings

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score


# ============================================================
# MACHINE LEARNING MODEL TRAINER
# ============================================================

class MachineLearningModel:

    MODEL_DIR = os.path.join(settings.BASE_DIR, "Model")

    def __init__(self):

        self.file_path = os.path.join(
            settings.BASE_DIR,
            "invest",
            "pesa",
            "pesa.csv"
        )

        self.df = pd.read_csv(self.file_path)

        self.feature_names = [
            "Liquidity",
            "Borrowed",
            "Invested",
            "Collateral",
            "Interest"
        ]

        self.target_name = "Rate"

        self.X = self.df[self.feature_names].copy()

        self.y = self.df[self.target_name]

        self.scaler = StandardScaler()

        self.X_scaled = self.scaler.fit_transform(self.X)

        self.model = LinearRegression()

        self.model.fit(
            self.X_scaled,
            self.y
        )

        os.makedirs(
            self.MODEL_DIR,
            exist_ok=True
        )

        joblib.dump(
            self.model,
            os.path.join(
                self.MODEL_DIR,
                "interest_model.pkl"
            )
        )

        joblib.dump(
            self.scaler,
            os.path.join(
                self.MODEL_DIR,
                "interest_scaler.pkl"
            )
        )

    # ----------------------------------------------------

    def accuracy(self):

        prediction = self.model.predict(
            self.X_scaled
        )

        mse = mean_squared_error(
            self.y,
            prediction
        )

        r2 = r2_score(
            self.y,
            prediction
        )

        return mse, r2


# ============================================================
# INTEREST RATE PREDICTOR
# ============================================================

class InterestRate:

    MODEL_DIR = os.path.join(settings.BASE_DIR, "Model")

    def __init__(self):

        self.model = joblib.load(
            os.path.join(
                self.MODEL_DIR,
                "interest_model.pkl"
            )
        )

        self.scaler = joblib.load(
            os.path.join(
                self.MODEL_DIR,
                "interest_scaler.pkl"
            )
        )

        self.features = None

    # ----------------------------------------------------

    def data_retrieval(
        self,
        liquidity,
        borrowed,
        invested,
        collateral,
        current_interest
    ):

        self.features = pd.DataFrame(
            [[
                float(liquidity),
                float(borrowed),
                float(invested),
                float(collateral),
                float(current_interest)
            ]],
            columns=[
                "Liquidity",
                "Borrowed",
                "Invested",
                "Collateral",
                "Interest"
            ]
        )

    # ----------------------------------------------------

    def data_preparation(self):

        scaled = self.scaler.transform(
            self.features
        )

        prediction = self.model.predict(
            scaled
        )

        predicted_rate = float(prediction[0])

        predicted_rate = round(
            predicted_rate,
            2
        )

        return predicted_rate

    # ----------------------------------------------------

    def predict(
        self,
        liquidity,
        borrowed,
        invested,
        collateral,
        current_interest
    ):

        self.data_retrieval(
            liquidity,
            borrowed,
            invested,
            collateral,
            current_interest
        )

        return self.data_preparation()