# Preventive Maintenance Dashboard

A Streamlit application developed for preventive maintenance monitoring at **Leoni Mateur Sud**.

## Features

- Upload and analyze preventive maintenance data from Excel.
- Display maintenance KPIs.
- Track machine defects.
- Visualize maintenance statistics.
- Generate interactive charts and tables.
- Search and filter maintenance records.

## Project Structure

```
.
├── app.py
├── analysis.py
├── defect_full_report_bol_702092.xlsx
├── leoni.png
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:

```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Create a virtual environment (optional):

```bash
python -m venv venv
```

Activate it:

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the application

```bash
streamlit run app.py
```

The application will be available at:

```
http://localhost:8501
```

## Data

The application uses the Excel file:

```
defect_full_report_bol_702092.xlsx
```

This file contains the preventive maintenance and defect records used for analysis.

## Technologies

- Python
- Streamlit
- Pandas
- Plotly
- OpenPyXL

## Author

Hamdi Abdeljawed
Master's Degree in Advanced Robotics and Artificial Intelligence
Bachelor's Degree in Electrical Engineering
