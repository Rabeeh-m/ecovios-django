# Ecovios

Ecovios is a full-featured e-commerce platform built using Django, designed specifically for selling resin jewellery. The platform provides a seamless shopping experience with features like product browsing, cart management, secure checkout, user authentication, order tracking, and more. It includes a robust backend for managing products, orders, and user data, along with a responsive frontend for an enhanced user experience.

## Features
- Product Catalog: Browse and search a wide range of resin jewellery products with detailed descriptions and images.
- Shopping Cart: Add, update, or remove items from the cart with real-time updates.
- Secure Checkout: Supports multiple payment methods, including Paypal, cash on delivery (COD) and wallet payments.
- User Authentication: Register, login, and manage user profiles with features like password reset and OTP verification.
- Order Management: View order history, track orders, and manage addresses.
- Wishlist: Save favorite products for future purchases.
- Coupon System: Apply discounts using coupons during checkout.
- Responsive Design: Fully responsive UI for seamless browsing on desktop and mobile devices.
- Admin Dashboard: Manage products, orders, and users through a comprehensive Django admin interface.

## Project Structure
```bash
Ecovios/
├── accounts/                    # App for user authentication and profile management
├── adminapp/                    # App for admin management
├── carts/                       # App for carts creation and management
├── category/                    # App for category management
├── ecovios/                     # Root directory, for configure entire project
├── orders/                      # App for order processing and management
├── store/                       # App for product catalog, cart, and wishlist
├── static/                      # Static files (CSS, JS, images, fonts)
├── staticfiles/                 # Collected static files for production
├── templates/                   # HTML templates for rendering pages
│   ├── accounts/                # Templates for user-related pages
│   ├── orders/                  # Templates for order-related pages
│   ├── store/                   # Templates for product and cart pages
│   └── includes/                # Reusable template components (navbar, footer, etc.)
├── manage.py                    # Django management script
└── requirements.txt             # Project dependencies
```


## Tech Stack
- Backend: Django (Python)
- Frontend: HTML, CSS, JavaScript, Bootstrap, Font Awesome
- Database: PostgreSQL
- Dependencies: Listed in requirements.txt

## Prerequisites
- Python 3.9+
- Django (version specified in requirements.txt)
- Git

## Installation

### 1. Clone the Repository:
```bash
git clone https://github.com/Rabeeh-m/ecovios-django.git
cd Ecovios
```

### 2. Set Up a Virtual Environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Collect Static Files:
```bash
python manage.py collectstatic
```

### 6. Run the Development Server:
```bash
python manage.py runserver
```

## Configuration
- Database: Configure the database in settings.py if using a database other than SQLite.
- Static Files: Ensure STATIC_ROOT and STATICFILES_DIRS are correctly set in settings.py for production.
- Email Settings: Configure email backend for password reset and order confirmation emails.
- Payment Integration: Update payment gateway settings in settings.py for production use.

## Contributing
- Fork the repository.
- Create a new branch (git checkout -b feature-branch).
- Make your changes and commit (git commit -m 'Add feature').
- Push to the branch (git push origin feature-branch).
- Open a Pull Request.
