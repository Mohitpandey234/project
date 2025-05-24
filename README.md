# Flask Chat Application

A modern chat application built with Flask, featuring:
- User authentication with OTP verification
- ChatGPT-like interface
- Modern, responsive design

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/Mohitpandey234/project.git
cd project
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python market.py
```

5. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Features
- Clean, modern UI inspired by ChatGPT
- Email and password authentication
- OTP verification system
- Responsive chat interface
- Auto-resizing message input
- Enter to send, Shift+Enter for new line

## Project Structure
```
├── market.py           # Main Flask application
├── requirements.txt    # Python dependencies
└── templates/         # HTML templates
    ├── home.html      # Landing page
    ├── auth.html      # Login/Register page
    ├── verify.html    # OTP verification page
    └── dashboard.html  # Chat interface
```

## License
MIT License
