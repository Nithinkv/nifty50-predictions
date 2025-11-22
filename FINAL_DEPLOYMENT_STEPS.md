# Final Step: Push to GitHub & Deploy

## ✅ Git is Ready Locally!

Your code is now committed locally. Now you need to push it to GitHub.

---

## Step 1: Create GitHub Repository

1. Go to: **https://github.com/new**
2. Fill in:
   - **Repository name:** `nifty50-predictions`
   - **Description:** "Real-time NIFTY 50 stock predictions using LightGBM ML model"
   - **Visibility:** Public
3. **Click "Create repository"**
4. **Copy the HTTPS URL** (looks like: `https://github.com/YOUR_USERNAME/nifty50-predictions.git`)

---

## Step 2: Push Code to GitHub

In PowerShell (in project folder), run:

```powershell
$env:Path += ";C:\Program Files\Git\bin"
cd "d:\Projects\Market analysiis"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nifty50-predictions.git
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

You'll be prompted to authenticate:
- Use GitHub token or personal access token
- Or use browser login

---

## Step 3: Deploy on Streamlit Cloud

1. Go to: **https://streamlit.io/cloud**
2. Click "New app"
3. Sign in with GitHub
4. Select:
   - **Repository:** `YOUR_USERNAME/nifty50-predictions`
   - **Branch:** `main`
   - **Main file:** `streamlit_app.py`
5. Click **"Deploy"**

Wait 2-3 minutes for build to complete.

---

## Step 4: Your Live App

Once deployed, you'll get a URL like:
```
https://your-username-nifty50-predictions.streamlit.app
```

**That's it! Your app is LIVE!** 🚀

Share this URL with anyone to access your NIFTY 50 prediction dashboard!

---

## Verify Everything Worked

✅ Check GitHub: https://github.com/YOUR_USERNAME/nifty50-predictions
✅ Check Streamlit: https://share.streamlit.io (your app should be listed)
✅ Test on phone: Visit your app URL

---

**Congratulations! Your ML-powered stock prediction app is now live on the internet!**
