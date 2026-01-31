# RentEase - Rental Management System MVP

A comprehensive rental management system built with Django 5.x, Bootstrap 5, and PostgreSQL.

## Features

### Authentication & User Management
- Custom user model with roles (Customer, Vendor, Admin)
- Customer signup with GSTIN and company information
- Role-based access control
- User profile management

### Product Management
- Product catalog with images
- Flexible rental pricing (hourly, daily, weekly)
- Product variants and attributes
- Stock management
- Vendor-specific product listings

### Rental Flow
- **Quotation/Cart System**: Add products with rental dates
- **Order Creation**: Convert quotation to rental order
- **Reservation Logic**: Prevents overbooking with date-range checks
- **Pickup Management**: Record when items are picked up
- **Return Processing**: Track returns with automatic late fee calculation

### Invoicing & Payments
- Auto-generated invoices
- GST calculation (18%)
- Security deposit management
- Mock payment system
- PDF-ready invoice format

### Customer Portal
- Browse products with search and filters
- Add items to cart with rental periods
- Place orders
- Track order status
- View and download invoices

### Vendor/Admin Dashboard
- Revenue statistics
- Most rented products report
- Recent orders overview
- Product management (CRUD)
- Order management
- Invoice and payment tracking

## Tech Stack

- **Backend**: Django 5.x
- **Frontend**: Bootstrap 5 (CDN), Django Templates
- **Database**: PostgreSQL
- **Forms**: django-bootstrap5, crispy-forms
- **PDF**: reportlab, django-weasyprint

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- pip

### Setup Steps

1. **Clone and navigate to project**
   ```powershell
   cd "c:\Users\Shrey\Desktop\Rental Management  System\main"
   ```

2. **Create and activate virtual environment** (if not already done)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL**
   - Create database:
     ```sql
     CREATE DATABASE rental_db;
     CREATE USER postgres WITH PASSWORD 'postgres';
     GRANT ALL PRIVILEGES ON DATABASE rental_db TO postgres;
     ```
   - Update `main/settings.py` DATABASES section with your PostgreSQL credentials

   **For development**: You can use SQLite by uncommenting the SQLite config in settings.py

5. **Run migrations**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```powershell
   python manage.py createsuperuser
   ```
   Follow prompts to set up admin account.

7. **Create static and media directories**
   ```powershell
   python manage.py collectstatic --noinput
   ```

8. **Run development server**
   ```powershell
   python manage.py runserver
   ```

9. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Initial Data Setup

### Create Sample Data via Admin Panel

1. Login to admin panel (http://127.0.0.1:8000/admin/)

2. **Create Product Attributes** (optional):
   - Navigate to "Product Attributes"
   - Add attributes like: Brand, Color, Size
   - Add values for each attribute

3. **Create Vendor User**:
   - Navigate to "Users"
   - Click "Add User"
   - Set role to "Vendor"
   - Fill in company details and GSTIN

4. **Create Products** (as vendor):
   - Logout and login as vendor, OR
   - Use admin panel to create products
   - Set vendor, pricing, stock, and publish status

5. **Create Customer Account**:
   - Visit http://127.0.0.1:8000/accounts/signup/
   - Fill in registration form with company and GSTIN info

## User Roles

### Customer
- Browse products
- Add to cart with rental dates
- Place orders
- Make payments
- Track orders
- View invoices

### Vendor
- Manage own products
- View dashboard with statistics
- Manage orders
- Process pickups and returns
- Record payments
- View reports

### Admin
- Full system access
- Manage all products and orders
- View comprehensive reports
- System settings

## Key Custom Logic

### Overbooking Prevention
Located in `rental/models.py` - `OrderLine.clean()`:
- Checks for date-range overlaps using PostgreSQL date queries
- Validates available stock for selected rental period
- Raises ValidationError if insufficient inventory

### Late Fee Calculation
Located in `rental/models.py` - `Return.calculate_late_fee()`:
- Compares return date with order line end dates
- Calculates days late × daily rate
- Automatically applied to invoice

### Rental Price Calculation
Located in `rental/models.py` - `Product.calculate_rental_price()`:
- Determines optimal pricing based on duration
- Prioritizes weekly → daily → hourly rates
- Returns calculated total

## Project Structure

```
main/
├── accounts/           # User authentication & profiles
│   ├── models.py      # Custom User model
│   ├── views.py       # Auth views
│   ├── forms.py       # Signup and profile forms
│   └── urls.py
├── rental/            # Core rental functionality
│   ├── models.py      # Product, Order, Invoice, etc.
│   ├── views.py       # Vendor/admin views
│   ├── forms.py       # Product and order forms
│   ├── admin.py       # Django admin configuration
│   └── urls.py
├── website/           # Customer-facing views
│   ├── views.py       # Product browsing, cart, checkout
│   └── urls.py
├── templates/
│   ├── base.html      # Base template with Bootstrap
│   ├── accounts/      # Auth templates
│   ├── rental/        # Vendor/admin templates
│   └── website/       # Customer templates
├── static/            # CSS, JS, images
├── media/             # Uploaded product images
└── main/
    ├── settings.py    # Project settings
    └── urls.py        # Root URL configuration
```

## Development Notes

### Adding New Features
1. Models → Migrations → Admin → Forms → Views → Templates → URLs

### Testing
- Create test users for each role
- Test full rental flow: Browse → Cart → Order → Payment → Pickup → Return
- Verify overbooking prevention
- Check late fee calculations

### Deployment Checklist
- [ ] Change SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Update ALLOWED_HOSTS
- [ ] Configure production database
- [ ] Set up static file serving (WhiteNoise/CDN)
- [ ] Configure email backend for real emails
- [ ] Set up SSL/HTTPS
- [ ] Configure real payment gateway

## API Endpoints

### Website (Customer)
- `/` - Homepage
- `/products/` - Product listing
- `/product/<id>/` - Product detail
- `/cart/` - Shopping cart
- `/checkout/` - Checkout
- `/orders/` - My orders
- `/order/<id>/` - Order detail
- `/invoice/<id>/` - View invoice
- `/payment/<id>/` - Payment page

### Rental (Vendor/Admin)
- `/rental/dashboard/` - Dashboard
- `/rental/products/` - Manage products
- `/rental/orders/` - Manage orders
- `/rental/orders/<id>/` - Order detail
- `/rental/orders/<id>/pickup/` - Record pickup
- `/rental/orders/<id>/return/` - Record return
- `/rental/orders/<id>/invoice/` - Invoice management

### Accounts
- `/accounts/signup/` - Customer signup
- `/accounts/login/` - Login
- `/accounts/logout/` - Logout
- `/accounts/profile/` - User profile

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running
- Check credentials in settings.py
- Ensure database exists

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL in settings.py

### Migration Errors
- Delete migration files (except __init__.py)
- Run `python manage.py makemigrations` again

### Import Errors
- Ensure all packages in requirements.txt are installed
- Check virtual environment is activated

## Future Enhancements
- Real payment gateway integration (Razorpay/Stripe)
- Email notifications for order updates
- SMS notifications
- Advanced reporting with charts
- Calendar view for bookings
- Product availability calendar
- Bulk product upload
- Customer reviews and ratings
- Discount coupons system
- Multi-currency support

## License
MIT License - Feel free to use for hackathons and projects

## Contact
For questions or issues, contact the development team.

---
Built with ❤️ for Hackathon MVP
