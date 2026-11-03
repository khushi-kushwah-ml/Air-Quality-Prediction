import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG
# =========================
BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Air Quality Monitoring",
    layout="wide",
    initial_sidebar_state="expanded"

)





# =========================
# HELPER FUNCTIONS
# =========================
def fetch(endpoint):
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
        return response.json()
    except Exception:
        return None


# =========================
# SIDEBAR
# =========================
st.sidebar.title("System Control")
st.sidebar.markdown("**Backend Status & Metrics**")

health = fetch("/health")
metrics = fetch("/metrics")

if health:
    st.sidebar.success(f"Status: {health.get('status', 'unknown')}")
    if "last_run" in health:
        st.sidebar.caption(f"Last Run: {health['last_run']}")
else:
    st.sidebar.error("Backend not reachable")

if metrics:
    st.sidebar.metric("Run Count", metrics["run_count"])
    st.sidebar.metric("Avg Duration (sec)", round(metrics["avg_duration"], 4))


# =========================
# MAIN DASHBOARD
# =========================
st.title("Air Quality Prediction Dashboard")

prediction = fetch("/prediction")

if not prediction or "message" in prediction:
    st.warning("No prediction available yet.")
    st.stop()

# =========================
# TOP METRICS
# =========================
col1, col2, col3 = st.columns(3)

col1.metric(
    label="Predicted Value",
    value=round(prediction["predicted_value"], 3)
)

prediction_time = datetime.fromisoformat(prediction["prediction_time"])
col2.metric(
    label="Prediction Time",
    value=prediction_time.strftime("%H:%M:%S")
)

stim_time = datetime.fromisoformat(prediction["stimulated_timestamp"])
col3.metric(
    label="Sensor Time",
    value=stim_time.strftime("%H:%M:%S")
)

st.divider()

# =========================
# SENSOR DATA
# =========================
st.subheader("Stimulated Sensor Values")

# sensor_df = pd.DataFrame(
#     prediction["stimulated_values"].items(),
#     columns=["Sensor", "Value"]
# )

sensor_values = prediction["stimulated_values"].copy()

# Remove timestamp from sensor readings
sensor_values.pop("timestamp", None)

sensor_df = pd.DataFrame(
    sensor_values.items(),
    columns=["Sensor", "Value"]
)

sensor_df["Value"] = pd.to_numeric(
    sensor_df["Value"],
    errors="coerce"
)

st.dataframe(
    sensor_df,
    width="stretch",
    hide_index=True
)

# =========================
# AUTO REFRESH
# =========================
st.caption("Auto-refresh every 10 seconds")
# st.experimental_rerun()

# st.rerun()
