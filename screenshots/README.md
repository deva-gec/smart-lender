# Screenshots

This folder contains application screenshots for project documentation and submission.

## Required Screenshots

| Filename | Description | How to Capture |
|----------|-------------|----------------|
| `home_page.png` | Home page with title, model metrics, and form | Open `http://localhost:8080` |
| `prediction_form.png` | Filled loan application form | Fill sample data before capturing |
| `approved_result.png` | Low-risk approval result | Use: Salaried, ₹5000 income, good credit |
| `rejected_result.png` | High-risk rejection result | Use: Self-employed, ₹1800 income, no credit |

## Sample Data for Screenshots

### Approved (Low Risk)
- Gender: Male
- Marital Status: Married
- Education: Graduate
- Employment: Salaried
- Income: ₹5,000
- Loan Amount: 120 (₹1,20,000)
- Loan Term: 360 months
- Credit History: Good
- Property Area: Urban

### Rejected (High Risk)
- Gender: Male
- Marital Status: Not Married
- Education: Not Graduate
- Employment: Self-Employed
- Income: ₹1,800
- Loan Amount: 150 (₹1,50,000)
- Loan Term: 360 months
- Credit History: No / Poor
- Property Area: Urban

## Capture Steps

1. Start the app: `python app.py`
2. Open http://localhost:8080 in your browser
3. Use macOS: `Cmd + Shift + 4` → select area
4. Use Windows: `Win + Shift + S` → select area
5. Save images with the exact filenames listed above

## Notes

- Recommended resolution: 1280×720 or higher
- Use the same browser theme (light mode) for consistency
- Screenshots are referenced in `README.md` and `docs/Smart_Lender_Project_Documentation.md`
