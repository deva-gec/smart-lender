"""ML prediction logic for Smart Lender."""

import json
import os

import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

model = None
label_encoder = None
model_metrics = None


def load_artifacts() -> None:
    global model, label_encoder, model_metrics

    model_path = os.path.join(MODELS_DIR, "xgboost_model.pkl")
    encoder_path = os.path.join(MODELS_DIR, "label_encoder.pkl")
    metrics_path = os.path.join(MODELS_DIR, "model_metrics.json")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            "Trained model not found. Run `python train_model.py` first."
        )

    model = joblib.load(model_path)
    label_encoder = joblib.load(encoder_path)

    if os.path.exists(metrics_path):
        with open(metrics_path, encoding="utf-8") as f:
            model_metrics = json.load(f)
    else:
        model_metrics = {"best_model": "XGBoost", "models": {}}


def predict_loan(form_data: dict) -> dict:
    row = {
        "Gender": form_data["gender"],
        "Married": form_data["married"],
        "Education": form_data["education"],
        "Self_Employed": form_data["self_employed"],
        "ApplicantIncome": float(form_data["applicant_income"]),
        "LoanAmount": float(form_data["loan_amount"]) / 1000.0,
        "Loan_Amount_Term": int(form_data["loan_term"]),
        "Credit_History": int(form_data["credit_history"]),
        "Property_Area": form_data["property_area"],
    }

    df = pd.DataFrame([row])
    prediction_enc = model.predict(df)[0]
    probabilities = model.predict_proba(df)[0]
    classes = label_encoder.classes_
    prob_map = {cls: float(prob) for cls, prob in zip(classes, probabilities)}

    prediction = label_encoder.inverse_transform([prediction_enc])[0]
    confidence = prob_map[prediction] * 100

    if prediction == "Y":
        if confidence >= 80:
            risk_level = "Low"
            recommendation = (
                "Fast-track approval recommended. Applicant shows strong "
                "repayment indicators."
            )
        else:
            risk_level = "Moderate"
            recommendation = (
                "Conditional approval. Standard verification recommended."
            )
    else:
        if confidence >= 75:
            risk_level = "High"
            recommendation = (
                "High-risk applicant detected. Further scrutiny and document "
                "verification required before proceeding."
            )
        else:
            risk_level = "Moderate-High"
            recommendation = (
                "Application flagged for manual review. Additional income "
                "verification advised."
            )

    return {
        "prediction": "Approved" if prediction == "Y" else "Rejected",
        "raw_prediction": prediction,
        "confidence": round(confidence, 1),
        "approval_probability": round(prob_map.get("Y", 0) * 100, 1),
        "default_probability": round(prob_map.get("N", 0) * 100, 1),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "applicant": row,
    }
