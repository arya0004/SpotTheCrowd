import streamlit as st
import cv2
import os
import tempfile
from ultralytics import YOLO
from PIL import Image
import numpy as np

model = YOLO("yolov8m.pt")

# Seat detection logic
def run_yolo_on_frame(frame):
    empty, occ = 0, 0
    results = model.predict(frame)
    result = results[0]

    for box in result.boxes:
        label = result.names[box.cls[0].item()]
        cords = [round(x) for x in box.xyxy[0].tolist()]
        prob = box.conf[0].item()

        if label == "chair":
            empty += 1
        if label == "bench":
            empty += 2
        if label == "person":
            occ += 1

        # Draw boxes
        cv2.rectangle(frame, (cords[0], cords[1]), (cords[2], cords[3]), (255, 0, 0), 2)
        cv2.putText(frame, f"{label} {prob:.2f}", (cords[0], cords[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return frame, empty, occ

# Streamlit UI
st.set_page_config(page_title="Spot the Crowd", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: white;'>🚍 Spot the Crowd</h1>
    <p style='text-align: center; color: white;'>Choose your mode of transport and upload an image or video to estimate crowd occupancy.</p>
""", unsafe_allow_html=True)

st.sidebar.header("Choose Options")
mode = st.sidebar.selectbox("Mode of Transport", ["Bus", "Train", "Metro"])

uploaded_file = st.sidebar.file_uploader("Upload Image or Video", type=["jpg", "jpeg", "png", "mp4", "avi", "mov"])

if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())

    st.subheader(f"Mode Selected: {mode}")

    if file_ext in [".jpg", ".jpeg", ".png"]:
        image = Image.open(tfile.name).convert("RGB")
        frame = np.array(image)
        result_img, empty, occ = run_yolo_on_frame(frame)

        st.image(result_img, channels="BGR", caption="Detected Image")
        st.success(f"Vacant Seats: {empty} | Occupied Seats: {occ}")

    elif file_ext in [".mp4", ".avi", ".mov"]:
        cap = cv2.VideoCapture(tfile.name)
        total_empty, total_occ = 0, 0
        stframe = st.empty()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame, empty, occ = run_yolo_on_frame(frame)
            total_empty += empty
            total_occ += occ
            stframe.image(frame, channels="BGR")

        cap.release()
        st.success(f"Total Vacant Seats: {total_empty} | Total Occupied Seats: {total_occ}")

    else:
        st.error("Unsupported file type.")

st.markdown("""
<style>
body {
    background-color: #042940;
}
</style>
""", unsafe_allow_html=True)
