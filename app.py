import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="3D Concrete Printing (3DCP) Wall Dashboard", layout="wide")

# ---- Title & Description ----
st.title("3D Concrete Printing (3DCP) Wall Dashboard")
st.markdown(
    """
    Welcome to the 3D Printed Concrete Wall Dashboard.  
    Use the **Run Pipeline** button to process data, then explore the interactive plots and tables below.
    """
)

# ---- Data Locations ----
DATA_DIR = "data"
DEFAULT_ALIGNED_CSV = os.path.join(DATA_DIR, "aligned_slice_summary_translated.csv")
DEFAULT_ECC_CSV = os.path.join(DATA_DIR, "aligned_slice_summary_with_eccentricity_and_angles.csv")
DEFAULT_MATRIX_IMG = os.path.join(DATA_DIR, "Validate Matrix Transformation.png")
DEFAULT_CENTROID_HTML = os.path.join(DATA_DIR, "centroid_drift_vertical_spline.html")
DEFAULT_ECC_HTML = os.path.join(DATA_DIR, "eccentricity_vs_height.html")

def get_all_slice_htmls(data_dir=DATA_DIR):
    slice_htmls = []
    for fname in os.listdir(data_dir):
        if re.match(r"slice_z=.*mm\.html$", fname):
            slice_htmls.append(os.path.join(data_dir, fname))
    def z_key(f):
        match = re.search(r"slice_z=([0-9]+)mm", f)
        return int(match.group(1)) if match else 0
    slice_htmls = sorted(slice_htmls, key=z_key)
    return slice_htmls

DEFAULT_SLICE_HTMLS = get_all_slice_htmls()

def load_text_html(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Always use data folder files
slice_files = DEFAULT_SLICE_HTMLS
slice_file_names = [os.path.basename(f) for f in DEFAULT_SLICE_HTMLS]
matrix_img_file = DEFAULT_MATRIX_IMG
df = pd.read_csv(DEFAULT_ALIGNED_CSV)
df_ecc = pd.read_csv(DEFAULT_ECC_CSV)
centroid_html_str = load_text_html(DEFAULT_CENTROID_HTML)
ecc_html_str = load_text_html(DEFAULT_ECC_HTML)

# ---- Simulate pipeline run (for consistent interface) ----
if 'run_pipeline' not in st.session_state:
    st.session_state['run_pipeline'] = False
if st.button("Run Pipeline"):
    with st.spinner("Processing data..."):
        import time
        time.sleep(2)
        st.success("Pipeline completed. See results below.")
        st.session_state['run_pipeline'] = True

if st.session_state.get('run_pipeline', False):

    # --- Sample Individual Slice Visualizations (HTML) ---
    st.header("Sample Individual Slice Visualizations (HTML)")

    if slice_files and len(slice_files) > 0:
        st.subheader("Select and View Slice HTML")
        selected = st.selectbox(
            "Select a slice HTML to view", slice_file_names
        )
        idx = slice_file_names.index(selected)
        html_content = load_text_html(slice_files[idx])

        # --- Clean Slice Header ---
        z_value = re.search(r"slice_z=(\d+)mm", selected)
        if z_value:
            st.subheader(f"Slice z={z_value.group(1)} mm")
        else:
            st.subheader(f"Slice: {selected}")

        st.components.v1.html(html_content, height=900, scrolling=True)

        st.subheader("Download Selected Slice HTML")
        st.download_button(
            f"Download {selected}", html_content, file_name=selected, mime="text/html"
        )
    else:
        st.info("No slice HTMLs found.")

    # --- Matrix Validation ---
    st.header("Matrix Validation: PCA Rotation and XY Translation")
    if matrix_img_file and os.path.exists(matrix_img_file):
        st.subheader("Matrix Transformation Validation Image")
        st.image(matrix_img_file, caption="Matrix Transformation Validation", width=900)  # set width here!
    else:
        st.info("No matrix validation image found.")

    # --- Summary Statistics Section ---
    st.header("Summary Statistics (Aligned Slice Summary - Translated)")

    if df is not None:
        st.subheader("Full Data Table")
        st.dataframe(df, use_container_width=True)

        st.subheader("Descriptive Statistics")
        st.dataframe(df.describe(), use_container_width=True)

        st.subheader("Max, Min, Mean, Variance, Std, Height")
        st.write("Max Area (mm2):", df["Area_mm2"].max())
        st.write("Min Area (mm2):", df["Area_mm2"].min())
        st.write("Mean Area (mm2):", df["Area_mm2"].mean())
        st.write("Area Variance (mm2):", df["Area_mm2"].var())
        st.write("Area Standard Deviation (mm2):", df["Area_mm2"].std())
        st.write("Max Height (mm):", df["Height_mm"].max())
        st.write("Min Height (mm):", df["Height_mm"].min())

        st.subheader("Download Aligned Summary CSV")
        st.download_button("Download aligned summary CSV", df.to_csv(index=False),
            file_name="aligned_slice_summary_translated.csv", mime="text/csv")
    else:
        st.info("No summary CSV found.")

    # --- Eccentricity and Angle Section ---
    st.header("Eccentricity and Angle Info & Table (Aligned Slice Summary with Eccentricity and Angles)")
    if df_ecc is not None:
        z_ref = df_ecc["Height_mm"].iloc[0]
        x_col = [col for col in df_ecc.columns if "centroid" in col.lower() and "x" in col.lower()]
        x_ref = df_ecc[x_col[0]].iloc[0] if x_col else 0.0
        max_ecc = df_ecc["eccentricity_mm"].max()
        max_ecc_idx = df_ecc["eccentricity_mm"].idxmax()
        max_ecc_z = df_ecc.loc[max_ecc_idx, "Height_mm"]
        angle_col = "angle_from_bottom_deg"
        max_ecc_angle = df_ecc.loc[max_ecc_idx, angle_col] if angle_col in df_ecc.columns else None

        st.subheader("Bottom Reference and Max Eccentricity")
        st.markdown(f"""
        <div style="background-color:#eaf6fb;padding:12px 18px;border-radius:12px;margin-bottom:15px;">
        <b>Bottom reference:</b> Z = <code>{z_ref:.2f} mm</code>, X = <code>{x_ref:.3f} mm</code><br>
        <b>Max eccentricity from bottom centroid:</b>
        <ul>
            <li><b>{max_ecc:.2f} mm</b> at Z = <b>{max_ecc_z:.2f} mm</b></li>
            <li>Corresponding angle: <b>{max_ecc_angle:.6f} degrees</b></li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Full Eccentricity and Angle CSV Table")
        st.dataframe(df_ecc, use_container_width=True)

        st.subheader("Download Eccentricity and Angle CSV")
        st.download_button(
            "Download eccentricity and angle CSV", df_ecc.to_csv(index=False),
            file_name="eccentricity_and_angle.csv", mime="text/csv"
        )
    else:
        st.info("No eccentricity CSV found.")

    # --- Interactive HTML Plots ---
    st.header("Interactive HTML Plots")

    st.subheader("Centroid Drift (Interactive HTML)")
    st.components.v1.html(centroid_html_str, height=1050, scrolling=True)

    st.subheader("Eccentricity vs Height (Interactive HTML)")
    st.components.v1.html(ecc_html_str, height=1050, scrolling=True)

    st.subheader("Print & Export Tips")
    st.markdown("""
    Tip: To export your dashboard to PDF for archiving, use your browser's Print function (Ctrl+P), and choose Save as PDF.  
    """)
else:
    st.info("Press Run Pipeline to view the results with built-in demo data.")
