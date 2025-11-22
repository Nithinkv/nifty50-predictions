# GitHub & Streamlit Cloud Deployment Guide

## Complete Step-by-Step Instructions

### Step 1: Install Git (If Not Already Installed)

**Windows:**
1. Download from: https://git-scm.com/download/win
2. Run installer, use default settings
3. Restart PowerShell/Terminal

**Mac:**
```bash
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install git
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Fill in:
   - **Repository name:** `nifty50-predictions`
   - **Description:** "Real-time NIFTY 50 stock predictions using LightGBM ML model"
   - **Visibility:** Public
   - Click "Create repository"

3. Copy the HTTPS URL (looks like: `https://github.com/YOUR_USERNAME/nifty50-predictions.git`)

### Step 3: Push Code to GitHub

Open PowerShell in your project folder (`d:\Projects\Market analysiis`) and run:

```powershell
# Initialize git repo
git init

# Configure git (one-time setup)
git config user.email "your-email@gmail.com"
git config user.name "Your Name"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: NIFTY 50 prediction dashboard"

# Rename branch to main
git branch -M main

# Add remote repository (REPLACE YOUR_USERNAME and REPO_URL)
git remote add origin https://github.com/YOUR_USERNAME/nifty50-predictions.git

# Push to GitHub
git push -u origin main
```

### Step 4: Verify on GitHub

1. Go to your GitHub repo: `https://github.com/YOUR_USERNAME/nifty50-predictions`
2. Verify all files are uploaded:
   - ✅ `streamlit_app.py`
   - ✅ `requirements.txt`
   - ✅ `.streamlit/config.toml`
   - ✅ `models/short_term_lgb_all.pkl`
   - ✅ `combined/` folder with parquet files
   - ✅ `README.md`

### Step 5: Deploy on Streamlit Cloud

1. **Create Streamlit Account:**
   - Go to: https://streamlit.io/cloud
   - Click "Sign up"
   - Sign in with GitHub account
   - Authorize Streamlit

2. **Deploy New App:**
   - Click "New app" button
   - Fill in:
     - **Repository:** `YOUR_USERNAME/nifty50-predictions`
     - **Branch:** `main`
     - **Main file path:** `streamlit_app.py`
   - Click "Deploy"

3. **Wait for Deployment:**
   - Build process takes 2-3 minutes
   - You'll see logs in real-time
   - Green checkmark = Success!

4. **Your Live App URL:**
   ```
   https://YOUR-USERNAME-nifty50-predictions.streamlit.app
   ```

### Step 6: Access on Phone

1. **Share with Others:**
   - Copy your app URL
   - Send to friends/family
   - Anyone can visit (no installation needed!)

2. **Access Anytime:**
   - Bookmark the URL
   - App updates automatically when you push new code

---

## Important: Project Structure for Cloud Deployment

Your repository **MUST** have this structure (it already does!):

```
nifty50-predictions/
├── streamlit_app.py              ✅ Main app
├── requirements.txt              ✅ Dependencies
├── README.md                     ✅ Documentation
├── .streamlit/
│   └── config.toml              ✅ Config
├── models/
│   └── short_term_lgb_all.pkl   ✅ Trained model
├── combined/                     ✅ Data files
│   ├── price_panel.parquet
│   ├── volume_panel.parquet
│   └── features_long.parquet
└── output/                       (optional)
    └── metrics_short.csv
```

---

## Troubleshooting Deployment

### Error: "ModuleNotFoundError: No module named 'streamlit'"

**Solution:** Check `requirements.txt` includes all packages:
```
pandas
numpy
lightgbm
scikit-learn
yfinance
streamlit
joblib
pyarrow
```

### Error: "FileNotFoundError: models/short_term_lgb_all.pkl"

**Solution:** Ensure model file is in repository:
```bash
# In PowerShell
ls models/short_term_lgb_all.pkl
```

If missing, run locally:
```bash
python train_short_term.py
git add models/
git commit -m "Add trained model"
git push
```

### Error: "No such file or directory: combined/features_long.parquet"

**Solution:** Ensure combined/ folder exists:
```bash
# Run locally to regenerate
python combine_data.py
python make_features.py
git add combined/
git commit -m "Add combined data files"
git push
```

### App runs slowly on first load

**Normal!** First deployment takes 3-5 minutes because:
- Installing all dependencies
- Loading model (~1.5 MB)
- Fetching 50 stocks of data

After first load, results are cached for 1 hour.

---

## Git Commands Cheat Sheet

```powershell
# Check status
git status

# See changes
git diff

# Stage specific file
git add streamlit_app.py

# Commit changes
git commit -m "Update signal thresholds"

# Push to GitHub
git push

# Pull latest changes
git pull

# View commit history
git log --oneline
```

---

## Continuous Updates

After deployment, updating is easy!

**Make a change locally:**
```powershell
# Edit any file (e.g., streamlit_app.py)

# Push changes
git add .
git commit -m "Update: describe your change"
git push
```

**Streamlit Cloud will automatically:**
1. Detect the push
2. Pull new code
3. Rebuild app
4. Deploy (1-2 minutes)

Your live app updates instantly!

---

## Sharing Your App

**Get the permanent URL:**
```
https://YOUR-USERNAME-nifty50-predictions.streamlit.app
```

**Share with:**
- Friends & family
- On social media
- In emails
- On WhatsApp

**Example message:**
```
Check out my NIFTY 50 stock predictions dashboard!
https://your-username-nifty50-predictions.streamlit.app

Uses ML to predict 5-day returns for all 50 stocks. 
Works on phone! 📈
```

---

## Next Steps

1. ✅ Install Git (if needed)
2. ✅ Create GitHub repo
3. ✅ Run git commands above
4. ✅ Deploy on Streamlit Cloud
5. ✅ Share your app URL!

---

## Need Help?

- **Git Issues:** https://git-scm.com/book/en/v2
- **GitHub Help:** https://docs.github.com
- **Streamlit Docs:** https://docs.streamlit.io
- **Streamlit Community:** https://discuss.streamlit.io

---

**Status:** Ready to Deploy! 🚀

Once you complete these steps, your app will be live and accessible from any device, anywhere!
