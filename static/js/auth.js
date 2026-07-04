import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
    getAuth,
    RecaptchaVerifier,
    signInWithPhoneNumber,
    GoogleAuthProvider,
    signInWithPopup,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const config = window.FIREBASE_CONFIG;
const ready = window.FIREBASE_READY;

let auth = null;
let confirmationResult = null;
let recaptchaVerifier = null;

function showMessage(text, type = "error") {
    const el = document.getElementById("auth-message");
    el.textContent = text;
    el.className = `alert alert-${type}`;
    el.classList.remove("hidden");
}

function hideMessage() {
    const el = document.getElementById("auth-message");
    el.classList.add("hidden");
}

async function sendTokenToBackend(idToken) {
    const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken }),
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || "Login failed");
    }
    window.location.href = "/dashboard";
}

function setupTabs() {
    document.querySelectorAll(".auth-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
            document.querySelectorAll(".auth-panel").forEach((p) => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(`${tab.dataset.tab}-panel`).classList.add("active");
            hideMessage();
        });
    });
}

function setupRecaptcha() {
    if (!auth) return;
    if (recaptchaVerifier) {
        recaptchaVerifier.clear();
    }
    recaptchaVerifier = new RecaptchaVerifier(auth, "recaptcha-container", {
        size: "normal",
        callback: () => hideMessage(),
    });
}

async function init() {
    setupTabs();

    if (!ready || !config.apiKey) {
        return;
    }

    const app = initializeApp(config);
    auth = getAuth(app);
    auth.languageCode = "en";

    setupRecaptcha();

    document.getElementById("send-otp-btn").addEventListener("click", async () => {
        hideMessage();
        const country = document.getElementById("country-code").value;
        const phone = document.getElementById("phone-input").value.replace(/\D/g, "");

        if (phone.length < 10) {
            showMessage("Enter a valid mobile number.");
            return;
        }

        const fullPhone = `${country}${phone}`;
        const btn = document.getElementById("send-otp-btn");
        btn.disabled = true;
        btn.textContent = "Sending OTP...";

        try {
            confirmationResult = await signInWithPhoneNumber(auth, fullPhone, recaptchaVerifier);
            document.getElementById("otp-section").classList.remove("hidden");
            showMessage("OTP sent to your mobile. Enter it below.", "success");
            btn.textContent = "Resend OTP";
        } catch (err) {
            showMessage(err.message || "Failed to send OTP.");
            setupRecaptcha();
        } finally {
            btn.disabled = false;
        }
    });

    document.getElementById("verify-otp-btn").addEventListener("click", async () => {
        hideMessage();
        const otp = document.getElementById("otp-input").value.trim();

        if (!confirmationResult) {
            showMessage("Please request an OTP first.");
            return;
        }
        if (otp.length < 6) {
            showMessage("Enter the 6-digit OTP.");
            return;
        }

        const btn = document.getElementById("verify-otp-btn");
        btn.disabled = true;
        btn.textContent = "Verifying...";

        try {
            const result = await confirmationResult.confirm(otp);
            const idToken = await result.user.getIdToken();
            await sendTokenToBackend(idToken);
        } catch (err) {
            showMessage(err.message || "Invalid OTP. Please try again.");
        } finally {
            btn.disabled = false;
            btn.textContent = "Verify & Sign In";
        }
    });

    document.getElementById("google-signin-btn").addEventListener("click", async () => {
        hideMessage();
        const btn = document.getElementById("google-signin-btn");
        btn.disabled = true;

        try {
            const provider = new GoogleAuthProvider();
            provider.setCustomParameters({ prompt: "select_account" });
            const result = await signInWithPopup(auth, provider);
            const idToken = await result.user.getIdToken();
            await sendTokenToBackend(idToken);
        } catch (err) {
            showMessage(err.message || "Google sign-in failed.");
        } finally {
            btn.disabled = false;
        }
    });
}

init();
