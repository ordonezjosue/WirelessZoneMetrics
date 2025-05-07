import streamlit as st
import pandas as pd
import numpy as np

# --- MUST BE FIRST Streamlit command ---
st.set_page_config(page_title="Sales Performance Extractor", layout="wide")

# --- Custom CSS for Color Scheme ---
st.markdown("""
    <style>
        body {
            background-color: #F0F4F8;
            color: #003366;
        }
        .header-container {
            display: flex;
            align-items: center;
            background-color: #003366;
            padding: 20px;
            border-radius: 10px;
            color: #FFFFFF;
            margin-bottom: 20px;
        }
        .header-container img {
            height: 60px;
            margin-right: 20px;
        }
        .header-container h1 {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }
        .header-container p {
            margin: 5px 0 0;
            font-size: 14px;
            color: #B0C4DE;
        }
        .stButton>button {
            background-color: #0073e6;
            color: #FFFFFF;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
        }
        .stButton>button:hover {
            background-color: #005bb5;
        }
        .footer-container {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: #003366;
            color: #FFFFFF;
            text-align: center;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Header Section with Logo ---
st.markdown("""
    <div class="header-container">
        <img src="elypse_logo.png" alt="Elypse Systems Logo">
        <div>
            <h1>Sales Performance Extractor</h1>
            <p>Analyze sales data and calculate commissions effortlessly</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Page Content ---
st.markdown("""
## Elypse Systems and Solutions

Welcome to the **Sales Performance Extractor Tool**. This tool allows you to upload monthly sales CSV data and receive:

- A clean, styled summary of key performance metrics
- Automated commission scorecards based on our internal point system
- Trend insights and GP breakdowns for all employees

Please enter the same password we use for Google Drive. This is to ensure that company performance data is protected and only visible to internal team members.
""")

password = st.text_input("Enter password to access this app:", type="password")
if st.button("Submit"):
    st.success("Access granted. Please proceed with the data upload.")

# --- Persistent Internal Login Button at Bottom ---
st.markdown("""
    <div class="footer-container">
        <a href="https://commcalc.streamlit.app/" target="_blank">
            Internal Login
        </a>
    </div>
""", unsafe_allow_html=True)
