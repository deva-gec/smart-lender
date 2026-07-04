# Firebase Setup for Smart Lender (Real OTP + Google Login)

Smart Lender uses **Firebase Authentication** for real-time mobile OTP and Google sign-in. Follow these steps once.

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Add project** → name it `smart-lender` → Continue
3. Disable Google Analytics (optional) → Create project

## 2. Enable Authentication Methods

1. Open **Authentication** → **Get started**
2. **Sign-in method** tab:
   - Enable **Phone** → Save
   - Enable **Google** → set support email → Save

## 3. Register Web App

1. Project **Settings** (gear icon) → **Your apps**
2. Click **Web** (`</>`) → nickname: `Smart Lender Web`
3. Copy the `firebaseConfig` values into your `.env` file

## 4. Download Service Account (Backend)

1. Project Settings → **Service accounts**
2. Click **Generate new private key**
3. Save the JSON file as `firebase-service-account.json` in the project root

## 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Firebase values:

```env
SECRET_KEY=your-random-secret-key
FIREBASE_API_KEY=AIza...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abc123
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

## 6. Authorized Domains

In Firebase Console → Authentication → Settings → **Authorized domains**:
- Add `localhost` (for local development)
- Add your production domain when deploying

## 7. Phone Auth Testing

- Firebase sends **real SMS OTP** to the phone number entered
- For testing, you can add test phone numbers in Firebase Console → Authentication → Sign-in method → Phone → **Phone numbers for testing**

## 8. Run the App

```bash
source venv/bin/activate
pip install -r requirements.txt
python train_model.py   # if not done already
python app.py
```

Open http://localhost:8080 → Login page with Mobile OTP and Google options.

## Data Storage

All user logins and loan applications are saved in:
```
data/smart_lender.db
```

Export your data anytime from **My Applications → Export JSON**.
