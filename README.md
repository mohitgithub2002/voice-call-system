# 📞 Fee Payment Reminder - Voice Call System

An automated voice call system to send **fee payment reminders** to students in Hindi. Built for Indian educational institutions to streamline fee collection through personalized voice calls.

---

## ✨ Features

- 📊 **Excel Integration** - Read student data from `.xlsx` files
- 🗣️ **Hindi TTS** - Automated Hindi voice messages for better reach
- 📱 **Vobiz API** - Uses Vobiz voice calling platform
- 🔄 **Bulk Calling** - Make calls to multiple students automatically
- 🧪 **Dry Run Mode** - Preview calls without actually dialing
- ⏱️ **Rate Limiting** - Configurable delay between calls
- 📋 **Call Tracking** - Get call UUIDs and status for each call

---

## 🛠️ Prerequisites

- Python 3.8+
- Vobiz API account ([Get started here](https://www.vobiz.ai/))
- A publicly accessible webhook URL (for Vobiz answer callbacks)

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fee-reminder
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Vobiz API Credentials
   VOBIZ_AUTH_ID=your_auth_id
   VOBIZ_AUTH_TOKEN=your_auth_token
   VOBIZ_CALLER_ID=your_caller_id
   VOBIZ_ANSWER_URL=https://your-domain.com/webhook/answer
   
   # Organization Name (shown in voice message)
   ORG_NAME=आपका स्कूल का नाम
   ```

---

## 📊 Excel File Format

Your Excel file should have the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `student_name` | Student's name | राहुल शर्मा |
| `phone_number` | Phone with country code | +919876543210 |
| `pending_fees` | Amount pending (₹) | 5000 |
| `due_date` | Payment due date | 15-02-2026 |

### Create a Sample File
```bash
python main.py --create-sample
```

This creates `sample_students.xlsx` with the correct format.

---

## 🚀 Usage

### Basic Usage
```bash
python main.py students.xlsx
```

### Dry Run (Preview without calling)
```bash
python main.py students.xlsx --dry-run
```

### Limit Number of Calls
```bash
python main.py students.xlsx --limit 5
```

### Custom Delay Between Calls
```bash
python main.py students.xlsx --delay 5
```

### All Options
```bash
python main.py --help
```

```
usage: main.py [-h] [--dry-run] [--limit LIMIT] [--delay DELAY] [--create-sample] [excel_file]

Send fee payment reminders via voice calls

positional arguments:
  excel_file       Path to Excel file with student data

options:
  -h, --help       show this help message and exit
  --dry-run        Show what would happen without making actual calls
  --limit LIMIT    Limit number of calls to make
  --delay DELAY    Delay between calls in seconds (default: 2)
  --create-sample  Create a sample Excel file and exit
```

---

## 📞 Voice Message Template

The system generates personalized Hindi messages:

```
नमस्ते [Student Name] जी,

यह [Organization Name] से बात हो रही है।

आपकी [Amount] रुपये की फीस बकाया है।

कृपया [Due Date] से पहले भुगतान करें।

धन्यवाद।
```

---

## 🔧 Project Structure

```
fee-reminder/
├── main.py              # Main CLI application
├── excel_reader.py      # Excel file parser
├── vobiz_caller.py      # Vobiz API integration
├── webhook_server.py    # Flask webhook server for call handling
├── exotel_caller.py     # Alternative: Exotel integration
├── twilio_caller.py     # Alternative: Twilio integration
├── requirements.txt     # Python dependencies
├── sample_students.xlsx # Sample Excel template
├── .env                 # Environment variables (not in git)
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## 🌐 Webhook Server

The webhook server handles Vobiz callbacks and generates TTS responses:

```bash
# Development
python webhook_server.py

# Production (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 webhook_server:app
```

> ⚠️ **Important**: The webhook URL must be publicly accessible. Use tools like [ngrok](https://ngrok.com/) for local development.

---

## 📡 API Integrations

This project supports multiple voice calling providers:

| Provider | Module | Status |
|----------|--------|--------|
| **Vobiz** | `vobiz_caller.py` | ✅ Primary |
| Exotel | `exotel_caller.py` | Available |
| Twilio | `twilio_caller.py` | Available |

To switch providers, modify the import in `main.py`.

---

## 🔐 Security Notes

- Never commit your `.env` file to version control
- Keep your API credentials secure
- Use environment variables for all sensitive data
- The `.gitignore` file already excludes `.env`

---

## 📋 Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP requests to Vobiz API |
| `openpyxl` | Reading Excel files |
| `python-dotenv` | Environment variable management |
| `flask` | Webhook server |
| `gunicorn` | Production WSGI server |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software owned by Goyal Tech.

---

## 📧 Support

For support, contact the development team at Goyal Tech.

---

## 🔮 Future Enhancements

- [ ] WhatsApp message integration
- [ ] SMS fallback for failed calls
- [ ] Web dashboard for call analytics
- [ ] Scheduled calling feature
- [ ] Multi-language support
- [ ] Call recording storage
