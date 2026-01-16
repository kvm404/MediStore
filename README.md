# 💊 MediStore

A modern, full-featured **Pharmacy Inventory Management System** built with Flask. Designed for small to medium pharmacy businesses to manage medicines, track inventory with batch-level control, process sales, and gain business insights through comprehensive reports.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

### 📦 Inventory Management
- **Medicine Catalog** - Add, edit, and organize medicines with categories
- **Batch Tracking** - Track individual batches with expiry dates and purchase prices
- **FEFO System** - First Expiry, First Out automatic batch selection during sales
- **Stock Alerts** - Low stock and out-of-stock warnings on dashboard

### 🛒 Sales Management
- **Quick Search** - Real-time medicine search with autocomplete
- **Cart System** - Add multiple items, adjust quantities before checkout
- **Unlisted Items** - Sell items not in catalog (loose medicines, accessories)
- **Receipt Printing** - Thermal printer-friendly receipt format
- **Customer Info** - Optional customer name and phone tracking

### 📊 Business Intelligence Reports
| Report | Description |
|--------|-------------|
| **Profit & Loss** | Revenue, costs, margins with interactive charts |
| **Top Sellers** | Best-selling products by quantity and revenue |
| **Profitable Products** | Products ranked by profit amount and margin % |
| **Category Performance** | Sales breakdown by category with pie chart |
| **Sales Trends** | This month vs last month comparison |
| **Dead Stock** | Items not sold in 30/60/90/180 days |
| **Margin Alerts** | Items sold below cost (at a loss) |

### 📋 Operational Reports
- **Sales Report** - Daily/weekly/monthly sales with date filters
- **Expiry Report** - Expired and soon-to-expire batches with value at risk
- **Stock Report** - Current stock levels across all medicines

---

## 🖥️ Screenshots

<details>
<summary>Click to view screenshots</summary>

### Dashboard
The main dashboard shows key metrics, alerts for low stock and expiring items, and recent sales.

### Sales Interface
Quick medicine search, cart management, and checkout in one streamlined interface.

### Business Reports
Interactive charts powered by Chart.js for visualizing business performance.

</details>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MediStore.git
   cd MediStore
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-migrate
   ```

4. **Initialize the database**
   ```bash
   flask db upgrade
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

### Seed Sample Data (Optional)
```bash
python seed_data.py
```

---

## 📁 Project Structure

```
MediStore/
├── run.py                 # Application entry point
├── seed_data.py           # Sample data generator
├── app/
│   ├── main.py            # App factory & configuration
│   ├── models/
│   │   ├── __init__.py    # Model exports
│   │   ├── category.py    # Category model
│   │   ├── medicine.py    # Medicine model
│   │   ├── batch.py       # Batch model (inventory)
│   │   └── sale.py        # Sale & SaleItem models
│   ├── routes/
│   │   ├── home.py        # Dashboard routes
│   │   ├── medicines.py   # Medicine CRUD routes
│   │   ├── categories.py  # Category CRUD routes
│   │   ├── sales.py       # Sales processing routes
│   │   ├── reports.py     # All report routes
│   │   └── api.py         # JSON API endpoints
│   └── templates/
│       ├── base.html      # Base layout with sidebar
│       ├── home.html      # Dashboard template
│       ├── medicines/     # Medicine templates
│       ├── categories/    # Category templates
│       ├── sales/         # Sales templates
│       └── reports/       # Report templates
├── instance/
│   └── app.db             # SQLite database
└── migrations/            # Database migrations
```

---

## 🗄️ Database Schema

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Category   │     │  Medicine   │     │    Batch    │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id          │◄────│ category_id │     │ id          │
│ name        │     │ id          │◄────│ medicine_id │
│ description │     │ name        │     │ batch_number│
└─────────────┘     │ generic_name│     │ expiry_date │
                    │ manufacturer│     │ mrp         │
                    │ packing_type│     │ purchase_   │
                    │ units_per_  │     │   price     │
                    │   pack      │     │ stock_qty   │
                    │ min_stock   │     └──────┬──────┘
                    └─────────────┘            │
                                               │
┌─────────────┐     ┌─────────────┐            │
│    Sale     │     │  SaleItem   │            │
├─────────────┤     ├─────────────┤            │
│ id          │◄────│ sale_id     │            │
│ sale_date   │     │ id          │            │
│ customer_   │     │ batch_id    │────────────┘
│   name      │     │ item_name   │ (nullable for unlisted)
│ customer_   │     │ quantity    │
│   phone     │     │ price_at_   │
│ total_amount│     │   sale      │
└─────────────┘     └─────────────┘
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | Database connection string | `sqlite:///app.db` |

### Setting Production Secret Key
```bash
export SECRET_KEY='your-super-secret-key-here'
```

---

## 📖 Usage Guide

### Adding a Medicine
1. Go to **Medicines** → **Add Medicine**
2. Fill in details (name, category, packing info)
3. Save the medicine
4. Add batches with stock, expiry date, and prices

### Processing a Sale
1. Go to **Sales** → **New Sale**
2. Search for medicines and add to cart
3. Adjust quantities as needed
4. Add unlisted items if required (e.g., loose tablets)
5. Enter customer info (optional)
6. Complete the sale
7. Print receipt if needed

### Viewing Reports
1. Go to **Reports** from the sidebar
2. Choose from Operational or Business Intelligence reports
3. Use filters to customize date ranges
4. View charts and export data as needed

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/medicines/search` | GET | Search medicines by name |
| `/api/medicines/<id>/batches` | GET | Get batches for a medicine |

### Search Example
```bash
curl "http://localhost:5000/api/medicines/search?q=paracetamol&limit=10"
```

---

## 🛠️ Development

### Running in Debug Mode
```bash
export FLASK_DEBUG=1
python run.py
```

### Database Migrations
```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework used
- [Bootstrap 5](https://getbootstrap.com/) - UI framework
- [Chart.js](https://www.chartjs.org/) - Beautiful charts
- [Bootstrap Icons](https://icons.getbootstrap.com/) - Icon library

---

<p align="center">
  Made with ❤️ for pharmacies everywhere
</p>
