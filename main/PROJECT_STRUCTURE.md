# 📁 Project File Structure

```
Rental Management System/
├── main/                                  # Django project root
│   ├── accounts/                          # User authentication app
│   │   ├── migrations/
│   │   │   └── 0001_initial.py           # User model migration
│   │   ├── __init__.py
│   │   ├── admin.py                       # User admin configuration
│   │   ├── apps.py
│   │   ├── forms.py                       # SignUpForm, UserProfileForm
│   │   ├── models.py                      # Custom User model
│   │   ├── tests.py
│   │   ├── urls.py                        # Auth URLs
│   │   └── views.py                       # signup, login, logout, profile
│   │
│   ├── rental/                            # Core rental functionality app
│   │   ├── migrations/
│   │   │   └── 0001_initial.py           # All rental models migration
│   │   ├── __init__.py
│   │   ├── admin.py                       # Complete admin config
│   │   ├── apps.py
│   │   ├── context_processors.py          # Cart context processor
│   │   ├── forms.py                       # 8 forms for products/orders
│   │   ├── models.py                      # 13 models with business logic
│   │   ├── tests.py
│   │   ├── urls.py                        # Vendor/admin URLs
│   │   └── views.py                       # Dashboard, management views
│   │
│   ├── website/                           # Customer-facing app
│   │   ├── migrations/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py                        # Public URLs
│   │   └── views.py                       # Product browsing, cart, checkout
│   │
│   ├── main/                              # Project settings
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py                    # ⭐ Main configuration
│   │   ├── urls.py                        # Root URL routing
│   │   └── wsgi.py
│   │
│   ├── templates/                         # HTML templates
│   │   ├── base.html                      # ⭐ Bootstrap base template
│   │   │
│   │   ├── accounts/                      # Authentication templates
│   │   │   ├── login.html
│   │   │   ├── profile.html
│   │   │   └── signup.html
│   │   │
│   │   ├── rental/                        # Vendor/admin templates
│   │   │   ├── dashboard.html             # ⭐ Statistics dashboard
│   │   │   ├── invoice_manage.html
│   │   │   ├── order_detail_manage.html
│   │   │   ├── order_manage.html
│   │   │   ├── payment_form.html
│   │   │   ├── pickup_form.html
│   │   │   ├── product_delete.html
│   │   │   ├── product_form.html
│   │   │   ├── product_manage.html
│   │   │   └── return_form.html
│   │   │
│   │   └── website/                       # Customer templates
│   │       ├── cart.html
│   │       ├── checkout.html
│   │       ├── home.html                  # ⭐ Homepage
│   │       ├── invoice.html
│   │       ├── my_orders.html
│   │       ├── order_detail.html
│   │       ├── payment.html
│   │       ├── payment_success.html
│   │       ├── product_detail.html
│   │       └── product_list.html
│   │
│   ├── static/                            # Static files (CSS, JS)
│   │   ├── css/
│   │   └── js/
│   │
│   ├── media/                             # User uploads (product images)
│   │
│   ├── db.sqlite3                         # ⭐ SQLite database
│   ├── manage.py                          # Django management script
│   ├── requirements.txt                   # ⭐ Python dependencies
│   ├── create_sample_data.py              # ⭐ Sample data script
│   ├── README.md                          # ⭐ Setup guide
│   ├── QUICKSTART.md                      # ⭐ Quick start guide
│   └── IMPLEMENTATION_SUMMARY.md          # ⭐ Implementation details
│
└── venv/                                  # Virtual environment (not tracked)
```

---

## 📄 Key Files Explained

### ⭐ Critical Files

#### Configuration & Setup
- **requirements.txt** - All Python packages needed
- **main/settings.py** - Django configuration (database, apps, middleware)
- **main/urls.py** - Root URL routing
- **manage.py** - Django CLI tool

#### Models (Business Logic)
- **accounts/models.py** - Custom User with roles
- **rental/models.py** - All 13 models including:
  - Product, Order, Invoice (main entities)
  - Overbooking prevention logic
  - Late fee calculation
  - Pricing algorithms

#### Views (Application Logic)
- **accounts/views.py** - Authentication (4 views)
- **website/views.py** - Customer portal (10 views)
- **rental/views.py** - Vendor/admin (15 views)

#### Templates (User Interface)
- **templates/base.html** - Bootstrap layout
- **templates/website/** - Customer-facing (10 templates)
- **templates/rental/** - Management (10 templates)
- **templates/accounts/** - Auth (3 templates)

#### Admin Configuration
- **accounts/admin.py** - User management
- **rental/admin.py** - Product/order management

### 📊 Database Files
- **db.sqlite3** - SQLite database (development)
- ***/migrations/** - Database migrations

### 📝 Documentation
- **README.md** - Complete setup guide
- **QUICKSTART.md** - Quick start with credentials
- **IMPLEMENTATION_SUMMARY.md** - Implementation details
- **PROJECT_STRUCTURE.md** - This file

### 🔧 Utility Scripts
- **create_sample_data.py** - Creates sample users & products

---

## 📊 Statistics

```
Total Files: 50+
Python Files: 25+
Templates: 25+
Models: 13
Views: 29
Forms: 10
URL Patterns: 30+
Lines of Code: ~4500+
```

---

## 🎯 Quick Navigation

### To modify...

**User authentication**
→ `accounts/views.py`, `accounts/forms.py`

**Product display**
→ `website/views.py`, `templates/website/product_*.html`

**Shopping cart**
→ `website/views.py` (cart_view), `rental/models.py` (Quotation)

**Order processing**
→ `rental/views.py`, `rental/models.py` (RentalOrder)

**Dashboard statistics**
→ `rental/views.py` (dashboard)

**Invoice generation**
→ `rental/models.py` (Invoice), `templates/website/invoice.html`

**UI styling**
→ `templates/base.html`, inline CSS in templates

**Database schema**
→ `*/models.py`, run `python manage.py makemigrations`

**URL routing**
→ `*/urls.py` files

**Admin panel**
→ `*/admin.py` files

---

## 🔍 Finding Specific Features

| Feature | Location |
|---------|----------|
| Overbooking prevention | `rental/models.py` → `OrderLine.clean()` |
| Late fee calculation | `rental/models.py` → `Return.calculate_late_fee()` |
| Dynamic pricing | `rental/models.py` → `Product.calculate_rental_price()` |
| Cart functionality | `rental/context_processors.py` |
| User roles | `accounts/models.py` → `User.is_customer()` etc. |
| Dashboard stats | `rental/views.py` → `dashboard()` |
| Payment processing | `website/views.py` → `payment_view()` |
| Invoice PDF | `templates/website/invoice.html` (print-ready) |

---

## 🚀 Development Workflow

1. **Models** → Define in `*/models.py`
2. **Migrations** → `python manage.py makemigrations`
3. **Apply** → `python manage.py migrate`
4. **Admin** → Register in `*/admin.py`
5. **Forms** → Create in `*/forms.py`
6. **Views** → Implement in `*/views.py`
7. **URLs** → Add to `*/urls.py`
8. **Templates** → Create in `templates/*/`
9. **Test** → Run server and verify

---

## 📝 Notes

- **Migration files** are auto-generated (don't edit manually)
- **Static files** use Bootstrap CDN (no local files needed)
- **Media files** are uploaded to `media/` directory
- **Database** is SQLite for development, PostgreSQL for production
- **Templates** use Django template language + Bootstrap 5

---

This structure follows Django best practices and is organized for:
- ✅ Easy navigation
- ✅ Scalability
- ✅ Team collaboration
- ✅ Maintainability
