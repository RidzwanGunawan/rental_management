{
    'name': 'Rental Management System',
    'version': '1.0.0',
    'category': 'Operations/Rental',
    'summary': 'Professional rental management system for products and equipment',
    'description': '''
        Professional Rental Management System
        =====================================
        
        Complete solution for managing rental business operations:
        
        Key Features:
        * Customer Management with credit tracking
        * Product/Equipment Inventory with maintenance scheduling
        * Rental Order Management with workflow automation
        * Pricing management (daily, weekly, monthly rates)
        * Payment tracking and late fee calculation
        * Analytics and reporting dashboards
        * Calendar scheduling and availability tracking
        * Document management and instructions
        
        Business Benefits:
        * Streamlined rental operations
        * Better customer relationship management
        * Automated workflow and notifications
        * Data-driven business insights
        * Professional customer experience
    ''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    
    # Dependencies
    'depends': ['base', 'web'],
    
    # Data Files
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/sequences.xml',
        
        # Views (URUTAN PENTING!)
        'views/rental_menu_views.xml',    
        'views/rental_customer_views.xml',  
        'views/rental_product_views.xml',
        'views/rental_order_views.xml',
        'views/rental_payment_wizard_views.xml',
    ],
    
    # Demo Data (optional)
    # 'demo': [
    #     'data/demo_customers.xml',
    #     'data/demo_products.xml',
    #     'data/demo_orders.xml',
    # ],
    
    # Static files
    'assets': {
        'web.assets_backend': [
            # 'rental_management/static/src/css/rental.css',
            # 'rental_management/static/src/js/rental_widgets.js',
        ],
    },
    
    # Application Configuration
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # Technical
    'sequence': 10,
    'post_init_hook': None,
    'uninstall_hook': None,
    
    # Images
    'images': [
        # 'static/description/banner.png',
        'static/description/icon.png',
    ],
}