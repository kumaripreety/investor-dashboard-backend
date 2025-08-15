# Investor Data Management API

A FastAPI-based backend service for managing investor data and commitments. This API provides endpoints for uploading CSV data, retrieving investor information, and analyzing investment commitments.

## 🚀 Features

- **CSV Data Upload**: Upload and process investor data from CSV files
- **Investor Management**: CRUD operations for investor data
- **Commitment Tracking**: Track and analyze investment commitments by asset class
- **Data Filtering**: Filter investors by various criteria
- **Asset Class Analytics**: Get insights into different asset classes
- **MongoDB Integration**: Robust data storage with MongoDB
- **API Documentation**: Auto-generated API docs with FastAPI

## 📋 Prerequisites

- Python 3.8+
- MongoDB 4.4+
- pip (Python package manager)

## 🛠️ Installation

### 1. Clone the Repository


### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start MongoDB
Make sure MongoDB is running on your system:

## 🏃‍♂️ Running the Application

The API will be available at:
- **API Base URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
investor-api/
├── apis/
│   ├── investors/
│   │   ├── investor_enums.py      # Enum definitions
│   │   ├── investor_models.py     # Pydantic models
│   │   ├── investor_routers.py    # API routes
│   │   └── investor_services.py   # Business logic
│   └── utils/
│       └── util_models.py         # Utility models
├── config/
│   └── setup.py                   # Configuration settings
├── dependencies/
│   └── mongo_db_client.py         # Database connection
├── main.py                        # FastAPI application entry point
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## 🔌 API Endpoints

### Upload Endpoints
- `POST /investors/upload-csv` - Upload investor data from CSV file

### Investor Endpoints
- `GET /investors/summary` - Get list of all investors with summaries
- `GET /investors/{investor_id}/details` - Get detailed investor information
- `GET /investors/asset-classes` - Get available asset classes
- `GET /investors/stats` - Get overall investment statistics
