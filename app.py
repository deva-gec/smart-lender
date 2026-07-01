"""Smart Lender — Flask web application for loan approval prediction."""

import json
import os

import joblib
import numpy as np
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-lender-dev-key")

FEATURE_COLUMNS = [
    "Gender",
    "Married",
    "Education",
    "Self_Employed",
    "ApplicantIncome",
    "LoanAmount",
    "Loan_Amount_Term",
    "Credit_History",
    "Property_Area",
]

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
        "LoanAmount": float(form_data["loan_amount"]),
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


@app.route("/")
def index():
    return render_template("index.html", metrics=model_metrics)


@app.route("/predict", methods=["POST"])
def predict():
    try:
        result = predict_loan(request.form)
        return render_template("result.html", result=result, metrics=model_metrics)
    except (ValueError, KeyError) as exc:
        flash(f"Invalid input: {exc}", "error")
        return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}


@app.route("/api/predict", methods=["POST"])
def api_predict():
    if not request.is_json:
        return {"error": "JSON body required"}, 400

    data = request.get_json()
    field_map = {
        "gender": "gender",
        "married": "married",
        "education": "education",
        "self_employed": "self_employed",
        "applicant_income": "applicant_income",
        "loan_amount": "loan_amount",
        "loan_term": "loan_term",
        "credit_history": "credit_history",
        "property_area": "property_area",
    }

    form_data = {}
    for api_key, form_key in field_map.items():
        if api_key not in data:
            return {"error": f"Missing field: {api_key}"}, 400
        form_data[form_key] = data[api_key]

    try:
        return predict_loan(form_data)
    except (ValueError, KeyError) as exc:
        return {"error": str(exc)}, 400


if __name__ == "__main__":
    load_artifacts()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
