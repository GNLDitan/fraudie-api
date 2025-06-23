# 1. Clone the repository
git clone https://github.com/your-username/gerald-ai.git
cd gerald-ai

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Add your environment variables
# Create a file named `.env` in the project root, and paste the following:

# .env
OPENAI_API_KEY=your-openai-key
PUSHOVER_TOKEN=your-pushover-app-token
PUSHOVER_USER=your-pushover-user-key

# 6. Add required files in the `me/` folder:
# - me/linkedin.pdf        ← your resume
# - me/summary.txt         ← a plain text summary of your background

# 7. Run the app
python main.py

# 8. Open in browser
# Gradio will automatically open the chatbot interface.
# If not, open http://127.0.0.1:7860 manually.
