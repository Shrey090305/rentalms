# 🚀 Quick Start Guide - RentEase

## ✅ System is Ready!

The Rental Management System is now fully set up and running!

### 🌐 Access URLs

- **Main Website**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Vendor Dashboard**: http://127.0.0.1:8000/rental/dashboard/

### 👤 Login Credentials

#### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Full system access, Django admin panel

#### Vendor Account
- **Username**: `vendor1`
- **Password**: `vendor123`
- **Access**: Product management, order processing, dashboard

#### Customer Account
- **Username**: `customer1`
- **Password**: `customer123`
- **Access**: Browse products, place orders, track rentals

---

## 🎯 Testing the Complete Flow

### As Customer:
1. **Browse Products**: Visit http://127.0.0.1:8000/products/
2. **View Product Details**: Click on any product
3. **Add to Cart**: 
   - Select rental dates (start and end)
   - Choose quantity
   - Add to cart
4. **Checkout**: 
   - Review cart
   - Enter delivery information
   - Place order
5. **Make Payment**: 
   - View order details
   - Click "Pay Now"
   - Complete mock payment
6. **Track Order**: View order status and invoice

### As Vendor/Admin:
1. **Login**: Use vendor1 credentials
2. **View Dashboard**: http://127.0.0.1:8000/rental/dashboard/
   - See statistics
   - View recent orders
   - Check most rented products
3. **Manage Products**:
   - Add new products
   - Edit existing products
   - Set pricing and inventory
4. **Manage Orders**:
   - View all orders
   - Update order status
   - Record pickup
   - Record return (with late fee calculation)
5. **Process Payments**:
   - View invoices
   - Record payments

---

## 📊 Sample Data Included

### Products (6 items):
- Professional Camera (₹3,000/day)
- Video Projector (₹2,000/day)
- Laptop Computer (₹1,500/day)
- Sound System (₹5,000/day)
- LED Lights (₹2,500/day)
- Drone with Camera (₹6,000/day)

### Users:
- 1 Admin
- 1 Vendor (owns all products)
- 1 Customer (ready to place orders)

---

## 🔧 Key Features to Test

### ✓ Overbooking Prevention
Try booking the same product for overlapping dates - the system will prevent it!

### ✓ Dynamic Pricing
The system calculates rental price based on duration (hourly/daily/weekly).

### ✓ Late Fee Calculation
When recording a return after the end date, late fees are automatically calculated.

### ✓ Invoice Generation
Automatic invoice creation with GST calculation and security deposit.

### ✓ Role-Based Access
- Customers see product catalog and cart
- Vendors see dashboard and management tools
- Admins have full access

---

## 🛠️ Development Commands

### Stop Server
Press `CTRL+C` in the terminal running the server

### Restart Server
```powershell
python manage.py runserver
```

### Create New Superuser
```powershell
python manage.py createsuperuser
```

### Access Django Shell
```powershell
python manage.py shell
```

### Make Migrations (after model changes)
```powershell
python manage.py makemigrations
python manage.py migrate
```

---

## 📁 Project Structure Overview

```
main/
├── accounts/          # User authentication
├── rental/            # Core rental logic
├── website/           # Customer-facing views
├── templates/         # HTML templates
│   ├── base.html     # Bootstrap layout
│   ├── accounts/     # Login, signup, profile
│   ├── rental/       # Vendor dashboard
│   └── website/      # Product catalog, cart
├── static/           # CSS, JS, images
├── media/            # Uploaded product images
└── db.sqlite3        # Database
```

---

## 🎨 UI Highlights

- **Responsive Design**: Bootstrap 5 with mobile support
- **Clean Navigation**: Role-based navbar
- **Modern Cards**: Product and dashboard cards
- **Status Badges**: Visual order status indicators
- **Interactive Forms**: Bootstrap-styled forms with validation
- **Icons**: Bootstrap Icons throughout

---

## 📝 Next Steps for Hackathon Demo

1. **Add Product Images**: 
   - Login as vendor
   - Edit products and upload images

2. **Create Sample Orders**:
   - Login as customer
   - Place 2-3 orders with different products
   - Process payments

3. **Test Management Flow**:
   - Login as vendor
   - Update order statuses
   - Record pickup and return

4. **Prepare Demo Script**:
   - Show customer journey
   - Show vendor dashboard
   - Highlight overbooking prevention
   - Demonstrate late fee calculation

---

## 🐛 Troubleshooting

### Server Won't Start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process if needed
taskkill /PID <PID> /F
```

### Static Files Not Loading
```powershell
python manage.py collectstatic --noinput
```

### Database Issues
```powershell
# Reset database (WARNING: deletes all data)
del db.sqlite3
python manage.py migrate
python create_sample_data.py
```

---

## 🚀 Ready for Hackathon!

Your Rental Management System MVP is complete with:
- ✅ End-to-end rental flow
- ✅ Role-based access (Customer, Vendor, Admin)
- ✅ Overbooking prevention
- ✅ Dynamic pricing
- ✅ Invoice generation
- ✅ Payment processing
- ✅ Dashboard & reports
- ✅ Responsive Bootstrap UI

**Server is running at**: http://127.0.0.1:8000/

Happy hacking! 🎉
