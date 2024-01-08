""""""
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# class PredictionModel:
#     """"""

#     def __init__(self):
#         """"""
#         # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#         self.model = LinearRegression()

#     async def train(self, X, y):
#         """"""
#         # self.model.fit(X_train, y_train)
#         print("PredictionModel train", X, y)
#         self.model.fit(X, y)

#     async def predict(self, nieuwe_waarden):
#         """"""
#         print("PredictionModel predict", nieuwe_waarden)
#         return self.model.predict(nieuwe_waarden)


# class Predictor:
#     """"""

#     def __init__(self, model):
#         """"""
#         self.model = model

#     async def predict(self, new_variables):
#         """"""
#         print("Predictor predict", new_variables)
#         return await self.model.predict(new_variables)


class ModelTrainer:
    """Modeltrainer."""

    def __init__(self, csv_file_path):
        """Init."""
        # print(csv_file_path)
        self.model = LinearRegression()
        self.csv_file_path = csv_file_path

    async def load_data(self):
        """Load data."""
        # print("load data", self.csv_file_path)
        try:
            data = pd.read_csv(self.csv_file_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"CSV file not found at path: {self.csv_file_path}"
            ) from e
        # required_columns = ["dd", "solar", "verbruik_zonder_verwarming"]
        # required_columns = ["dd", "solar", "hour"]
        # if not set(required_columns).issubset(data.columns):
        #     raise ValueError(
        #         f"CSV file should contain the following columns: {', '.join(required_columns)}"
        #     )
        return data

        # return pd.read_csv(self.csv_file_path, parse_dates=["timestamp"])

    async def prepare_data(self, data, independent_variables, dependent_variable):
        """Prepare data."""
        # Definieer de onafhankelijke variabelen ('dd', 'solar', 'verbruik_zonder_verwarming') en de afhankelijke variabele ('hour')
        # X = data[["dd", "solar", "verbruik_zonder_verwarming"]].values
        # print(independent_variables)
        # print(dependent_variable)
        X = data[independent_variables].values
        y = data[dependent_variable].values
        # X = data[["dd", "solar"]].values
        # y = data["hour"].values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        # print("X", X)
        # print("y", y)
        # print("X_train", X_train)
        # print("y_train", y_train)
        return X_train, y_train

    async def train(self, X, y):
        """Train."""
        # self.model.fit(X_train, y_train)
        # print("ModelTrainer train", X, y)
        self.model.fit(X, y)

    async def predict(self, new_variables):
        """Predict."""
        # print("ModelTrainer predict", new_variables)
        return self.model.predict(new_variables)
