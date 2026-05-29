"""Module for interacting with the LightGBM machine learning app.

This module provides functionality to:
- Train LightGBM models via the app API
- Check if a model is trained
- Make predictions using trained models
"""

import base64

import aiohttp
import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

from .const import DEFAULT_APP_HOSTNAME, log


class LGBM:
    """Class to interact with machine-learner app."""

    def __init__(self, modelname: str, hostname: str | None = None) -> None:
        """Initialize LGBM client.

        Args:
            modelname: Unique identifier for the model.
            hostname: App hostname (defaults to localhost:14760).
        """
        self.modelname = modelname
        self.hostname = hostname or DEFAULT_APP_HOSTNAME

    def _df_to_arrow(self, df: pd.DataFrame) -> str:
        """Serialize a DataFrame to a base64-encoded Arrow IPC stream."""
        buf = pa.BufferOutputStream()
        writer = ipc.new_stream(buf, pa.Schema.from_pandas(df))
        writer.write_table(pa.Table.from_pandas(df))
        writer.close()
        return base64.b64encode(buf.getvalue().to_pybytes()).decode()

    async def train(self, df: pd.DataFrame, target_column: str) -> dict:
        """Train a model.

        Args:
            df: Training data with features and target column.
            target_column: Name of the column to predict.

        Returns:
            Response from training endpoint.

        Raises:
            aiohttp.ClientError: If connection to app fails.
            ValueError: If training fails on the app side.
        """

        data = {
            "model_name": self.modelname,
            "target_column": target_column,
            "dataframe": self._df_to_arrow(df),
            "format": "arrow",
        }
        # data = {
        #     "model_name": self.modelname,
        #     "target_column": target_column,
        #     "dataframe": df.to_csv(index=False),
        # }

        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for training

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.hostname}/train", json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(
                            f"Training failed with status {response.status}: {error_text}"
                        )

                    content = await response.json()
                    log.debug("Trained model %s. Response: %s", self.modelname, content)
                    return content

        except aiohttp.ClientError as e:
            log.error("Failed to connect to app at %s: %s", self.hostname, e)
            raise
        except Exception as e:
            log.error("Unexpected error during training: %s", e)
            raise

    async def is_trained(self) -> bool:
        """Check if there is currently a trained model for this learner.

        Returns:
            True if model is trained, False otherwise.

        Raises:
            aiohttp.ClientError: If connection to app fails.
        """
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{self.hostname}/is_trained?model_name={self.modelname}"
                ) as response:
                    if response.status != 200:
                        log.warning(
                            "is_trained check failed with status %s", response.status
                        )
                        return False

                    data = await response.json()
                    log.debug("is_trained check for %s: %s", self.modelname, data)
                    return data.get("is_trained", False)

        except aiohttp.ClientError as e:
            log.error("Failed to connect to app at %s: %s", self.hostname, e)
            raise
        except Exception as e:
            log.error("Unexpected error checking model status: %s", e)
            return False

    async def predict(self, df: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """Use the trained model to predict values.

        Args:
            df: Input data with features.
            target_column: Name of the column to predict.

        Returns:
            DataFrame with predictions indexed by original df index.

        Raises:
            aiohttp.ClientError: If connection to app fails.
            ValueError: If prediction fails.
        """
        timeout = aiohttp.ClientTimeout(total=60)
        data = {
            "model_name": self.modelname,
            "dataframe": self._df_to_arrow(df),
            "format": "arrow",
        }

        try:
            log.debug("predicting with model %s", self.modelname)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.hostname}/predict", json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(
                            f"Prediction failed with status {response.status}: {error_text}"
                        )

                    result = await response.json()

                    prediction = pd.DataFrame(index=df.index)
                    prediction[target_column] = result["predictions"]

                    return prediction

        except aiohttp.ClientError as e:
            log.error("Failed to connect to app at %s: %s", self.hostname, e)
            raise
        except Exception as e:
            log.error("Unexpected error during prediction: %s", e)
            raise
