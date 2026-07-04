"""Smart Lender — Flask application with auth and data persistence."""

import os

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import (
    current_user_id,
    init_firebase,
    login_required,
    login_user,
    logout_user,
    verify_firebase_token,
)
from database import (
    export_user_data,
    get_user_applications,
    get_user_by_id,
    init_db,
    save_application,
    upsert_user,
)
import predictor
from predictor import load_artifacts, predict_loan

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-lender-dev-key-change-me")
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7


def firebase_client_config() -> dict:
    return {
        "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID", ""),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": os.environ.get("FIREBASE_APP_ID", ""),
    }


def firebase_ready() -> bool:
    cfg = firebase_client_config()
    return bool(cfg["apiKey"] and cfg["projectId"] and init_firebase())


@app.context_processor
def inject_globals():
    user = get_user_by_id(current_user_id()) if current_user_id() else None
    return {
        "current_user": user,
        "firebase_config": firebase_client_config(),
        "firebase_ready": firebase_ready(),
        "metrics": predictor.model_metrics,
    }


@app.route("/")
def root():
    if current_user_id():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login")
def login():
    if current_user_id():
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    if not request.is_json:
        return jsonify({"error": "JSON body required"}), 400

    data = request.get_json()
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "idToken is required"}), 400

    try:
        decoded = verify_firebase_token(id_token)
    except Exception as exc:
        return jsonify({"error": f"Authentication failed: {exc}"}), 401

    firebase_uid = decoded["uid"]
    phone = decoded.get("phone_number")
    email = decoded.get("email")
    name = decoded.get("name") or decoded.get("display_name")
    picture = decoded.get("picture")

    if phone:
        provider = "phone"
    elif decoded.get("firebase", {}).get("sign_in_provider") == "google.com":
        provider = "google"
    else:
        provider = decoded.get("firebase", {}).get("sign_in_provider", "firebase")

    user = upsert_user(
        firebase_uid=firebase_uid,
        auth_provider=provider,
        phone=phone,
        email=email,
        display_name=name,
        photo_url=picture,
    )
    login_user(user)

    return jsonify(
        {
            "success": True,
            "user": {
                "id": user["id"],
                "display_name": user.get("display_name"),
                "phone": user.get("phone"),
                "email": user.get("email"),
                "auth_provider": user.get("auth_provider"),
            },
        }
    )


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    applications = get_user_applications(current_user_id(), limit=5)
    return render_template("dashboard.html", recent_applications=applications)


@app.route("/history")
@login_required
def history():
    applications = get_user_applications(current_user_id(), limit=100)
    return render_template("history.html", applications=applications)


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        result = predict_loan(request.form)
        application_id = save_application(current_user_id(), request.form, result)
        result["application_id"] = application_id
        return render_template("result.html", result=result)
    except (ValueError, KeyError) as exc:
        flash(f"Invalid input: {exc}", "error")
        return redirect(url_for("dashboard"))


@app.route("/api/my-applications")
@login_required
def api_my_applications():
    return jsonify(get_user_applications(current_user_id()))


@app.route("/api/export-my-data")
@login_required
def api_export_my_data():
    return jsonify(export_user_data(current_user_id()))


@app.route("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
        "firebase_ready": firebase_ready(),
        "database": "sqlite",
    }


@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    if not request.is_json:
        return jsonify({"error": "JSON body required"}), 400

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
            return jsonify({"error": f"Missing field: {api_key}"}), 400
        form_data[form_key] = data[api_key]

    try:
        result = predict_loan(form_data)
        application_id = save_application(current_user_id(), form_data, result)
        result["application_id"] = application_id
        return jsonify(result)
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400


def create_app():
    init_db()
    load_artifacts()
    init_firebase()
    return app


if __name__ == "__main__":
    create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
