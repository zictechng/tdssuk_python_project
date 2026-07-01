from django.urls import path
from . import views


urlpatterns = [
    # public urls
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/forget-password/', views.forgotPassword, name='forgotPassword'),
    path('auth/reset-password/', views.resetForgotPassword, name='resetForgotPassword'),
    path('track/',               views.public_shipment_tracking, name='public_tracking'),
    

    # protected urls
    path('', views.dashboard, name='dashboard'), 
    path('contact/', views.contact_page, name='contact_page'), 
    path('quote/', views.quote_request, name='quote_request'),
    path('quote-message/<uuid:uuid>/', views.quote_message, name='quote_message'),
    path('quote-request/status/<uuid:uuid>/<str:status>/', views.update_quote_status,
    name='update_quote_status'
    ), 
    path('deleted-quote/', views.deletedQuote_request, name='deletedQuote_request'),
    
    path('view/quote-details/<uuid:uuid>/', views.viewQuoteDetails,
    name='viewQuoteDetails'), 

    path('pending-quote/', views.pendingQuote_request, name='pendingQuote_request'),
    path('approved-quote/', views.approvedQuote_request, name='approvedQuote_request'),
    path('rejected-quote/', views.rejectedQuote_request, name='rejectedQuote_request'),
    path('order/', views.order_list, name='order_list'),

    path('create-order/', views.createNew_order, name='createNew_order'),
    path('view/order-details/<uuid:uuid>/', views.viewOrderDetail, name='viewOrderDetail'),
    path('order/<uuid:uuid>/edit/', views.order_edit, name='order_edit'),

    path('order/<uuid:uuid>/images/upload/', views.order_image_upload, name='order_image_upload'),
    path('order/image/<int:image_id>/delete/', views.order_image_delete, name='order_image_delete'),
    
    path('cancelled-order/', views.orderCancelled_list, name='orderCancelled_list'),
    path('completed-order/', views.orderCompleted_list, name='orderCompleted_list'),
    path('deleted-order/', views.orderDeleted_list, name='orderDeleted_list'),
    path('order-in-transit/', views.orderIn_transit_list, name='orderIn_transit_list'),
    path('processing-order/', views.orderProcessing_list, name='orderProcessing_list'),
    path('return-order/', views.orderReturned_list, name='orderReturned_list'),

    path('shipments/', views.shipment_list, name='shipment_list'),
    path('shipments/pending/', views.shipment_list, {'status': 'pending'}, name='shipmentPending_list'),
    path('shipments/in-transit/', views.shipment_list, {'status': 'in_transit'}, name='shipmentInTransit_list'),
    path('shipments/delivered/', views.shipment_list, {'status': 'delivered'}, name='shipmentDelivered_list'),
    path('shipments/cancelled/', views.shipment_list, {'status': 'cancelled'}, name='shipmentCancelled_list'),
    path('shipments/returned/', views.shipment_list, {'status': 'returned'}, name='shipmentReturned_list'),

    path('shipments/create/', views.shipment_create, name='createNew_shipment'),
    path('shipments/<uuid:uuid>/', views.shipment_detail, name='viewShipmentDetail'),
    path('shipments/<uuid:uuid>/status/', views.shipment_change_status, name='shipmentChangeStatus'),

    # AJAX endpoint the create form calls when an order is selected
    # path('shipments/order-summary/<uuid:order_uuid>/', views.order_summary_partial, name='orderSummaryPartial'),

    # urls.py — Fleet Management

    # All Vehicles
    path('fleet/vehicles/', views.vehicle_list, name='vehicle_list'),
    path('fleet/vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('fleet/vehicles/<uuid:uuid>/', views.vehicle_detail, name='vehicle_detail'),
    path('fleet/vehicles/<uuid:uuid>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('fleet/vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),

    # Vehicle Maintenance
    path('fleet/maintenance/', views.maintenance_list, name='maintenance_list'),
    path('fleet/maintenance/create/', views.maintenance_create, name='maintenance_create'),
    path('fleet/maintenance/<int:pk>/delete/', views.maintenance_delete, name='maintenance_delete'),

    # Fuel Records
    path('fleet/fuel/', views.fuel_list, name='fuel_list'),
    path('fleet/fuel/create/', views.fuel_create, name='fuel_create'),
    path('fleet/fuel/<int:pk>/delete/', views.fuel_delete, name='fuel_delete'),

    # Route Planning
    path('fleet/routes/', views.route_list, name='route_list'),
    path('fleet/routes/create/', views.route_create, name='route_create'),
    path('fleet/routes/<uuid:uuid>/', views.route_detail, name='route_detail'),
    path('fleet/routes/<int:pk>/delete/', views.route_delete, name='route_delete'),

    # Fleet Reports
    path('fleet/reports/', views.fleet_reports, name='fleet_reports'),
    path('fleet/reports/cost/', views.fleet_reports_cost, name='fleet_reports_cost'),

    # Warehouse Management
    path('warehouse/', views.warehouse_list, name='warehouse_list'),
    path('warehouse/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouse/<uuid:uuid>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouse/<uuid:uuid>/edit/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouse/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),

    # Inventory Management
    path('warehouse/inventory/', views.inventory_list, name='inventory_list'),
    path('warehouse/inventory/create/', views.inventory_create, name='inventory_create'),
    path('warehouse/inventory/<uuid:uuid>/', views.inventory_detail, name='inventory_detail'),
    path('warehouse/inventory/<uuid:uuid>/edit/', views.inventory_edit, name='inventory_edit'),
    path('warehouse/inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),

    # Stock Movement
    path('warehouse/stock-movement/', views.stock_movement_list, name='stock_movement_list'),
    path('warehouse/stock-movement/create/', views.stock_movement_create, name='stock_movement_create'),
    path('warehouse/stock-movement/<int:pk>/delete/', views.stock_movement_delete, name='stock_movement_delete'),

    # Storage Locations
    path('warehouse/locations/', views.storage_location_list, name='storage_location_list'),
    path('warehouse/locations/create/', views.storage_location_create, name='storage_location_create'),
    path('warehouse/locations/<int:pk>/delete/', views.storage_location_delete, name='storage_location_delete'),

    # Warehouse Reports
    path('warehouse/reports/', views.warehouse_reports, name='warehouse_reports'),
    path('warehouse/reports/summary/', views.warehouse_reports_summary, name='warehouse_reports_summary'),
        
    #— Finance Management

    # Customer Invoices
    path('finance/invoices/', views.invoice_list, name='invoice_list'),
    path('finance/invoices/create/', views.invoice_create, name='invoice_create'),
    path('finance/invoices/<uuid:uuid>/', views.invoice_detail, name='invoice_detail'),
    path('finance/invoices/<uuid:uuid>/edit/', views.invoice_edit, name='invoice_edit'),
    path('finance/invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('finance/invoices/<uuid:uuid>/line-item/', views.invoice_add_line_item, name='invoice_add_line_item'),
    path('finance/invoices/line-item/<int:pk>/delete/', views.invoice_delete_line_item, name='invoice_delete_line_item'),
    path('finance/invoices/<uuid:uuid>/status/', views.invoice_update_status, name='invoice_update_status'),

    # Payments
    path('finance/payments/', views.payment_list, name='payment_list'),
    path('finance/payments/create/', views.payment_create, name='payment_create'),
    path('finance/payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # Freight Charges
    path('finance/freight/', views.freight_charge_list, name='freight_charge_list'),

    # Customs & Duty
    path('finance/customs/', views.customs_duty_list, name='customs_duty_list'),
    path('finance/customs/create/', views.customs_duty_create, name='customs_duty_create'),
    path('finance/customs/<int:pk>/delete/', views.customs_duty_delete, name='customs_duty_delete'),

    # Expenses
    path('finance/expenses/', views.expense_list, name='expense_list'),
    path('finance/expenses/create/', views.expense_create, name='expense_create'),
    path('finance/expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    # Agent Commissions
    path('finance/commissions/', views.agent_commission_list, name='agent_commission_list'),
    path('finance/commissions/create/', views.agent_commission_create, name='agent_commission_create'),
    path('finance/commissions/<int:pk>/delete/', views.agent_commission_delete, name='agent_commission_delete'),

    # Exchange Rates
    path('finance/exchange-rates/', views.exchange_rate_list, name='exchange_rate_list'),
    path('finance/exchange-rates/create/', views.exchange_rate_create, name='exchange_rate_create'),
    path('finance/exchange-rates/<int:pk>/delete/', views.exchange_rate_delete, name='exchange_rate_delete'),

    # Financial Reports
    path('finance/reports/', views.finance_reports, name='finance_reports'),

    # ============================================================
    # Customs Shipping Documents
    # ============================================================

    # Customs Documentation
    path('customs/documents/', views.customs_document_list, name='customs_document_list'),
    path('customs/documents/create/', views.customs_document_create, name='customs_document_create'),
    path('customs/documents/<uuid:uuid>/', views.customs_document_detail, name='customs_document_detail'),
    path('customs/documents/<uuid:uuid>/edit/', views.customs_document_edit, name='customs_document_edit'),
    path('customs/documents/<int:pk>/delete/', views.customs_document_delete, name='customs_document_delete'),

    # Import Shipments
    path('customs/imports/', views.import_shipment_list, name='import_shipment_list'),

    # Export Shipments
    path('customs/exports/', views.export_shipment_list, name='export_shipment_list'),

    # Customs Status Update (used on shipment detail page)
    path('customs/shipments/<uuid:uuid>/customs-status/', views.shipment_update_customs_status, name='shipment_update_customs_status'),

    # Duty & Tax Management
    path('customs/duty-tax/', views.duty_tax_list, name='duty_tax_list'),
    path('customs/duty-tax/create/', views.duty_tax_create, name='duty_tax_create'),
    path('customs/duty-tax/<int:pk>/delete/', views.duty_tax_delete, name='duty_tax_delete'),

    # ──────────────────────────────────────────
    # Documents Module URLs
    # ──────────────────────────────────────────

    # Shipping Labels
    path('documents/shipping-labels/', views.shipping_label_list, name='shipping_label_list'),
    path('documents/shipping-labels/<uuid:uuid>/', views.shipping_label_detail, name='shipping_label_detail'),

    # Invoices (print-ready)
    path('documents/invoices/', views.document_invoice_list, name='document_invoice_list'),
    path('documents/invoices/<uuid:uuid>/', views.document_invoice_detail, name='document_invoice_detail'),

    # Delivery Notes
    path('documents/delivery-notes/', views.delivery_note_list, name='delivery_note_list'),
    path('documents/delivery-notes/<uuid:uuid>/', views.delivery_note_detail, name='delivery_note_detail'),

    # Customs Forms
    path('documents/customs-forms/', views.document_customs_list, name='document_customs_list'),
    path('documents/customs-forms/<uuid:uuid>/', views.document_customs_detail, name='document_customs_detail'),

    # Uploaded Documents
    path('documents/uploaded/', views.uploaded_document_list, name='uploaded_document_list'),
    path('documents/uploaded/create/', views.uploaded_document_create, name='uploaded_document_create'),
    path('documents/uploaded/<uuid:uuid>/', views.uploaded_document_detail, name='uploaded_document_detail'),
    path('documents/uploaded/<uuid:uuid>/edit/', views.uploaded_document_edit, name='uploaded_document_edit'),
    path('documents/uploaded/<uuid:uuid>/delete/', views.uploaded_document_delete, name='uploaded_document_delete'),

    # ============================================================
    # USER MANAGEMENT
    # ============================================================
    path('users/',                                   views.user_list,               name='user_list'),
    path('users/create/',                            views.user_create,             name='user_create'),
    path('users/deleted/',                           views.user_deleted_list,       name='user_deleted_list'),  # ← must be before <uuid>
    path('users/<uuid:uuid>/',                       views.user_detail,             name='user_detail'),
    path('users/<uuid:uuid>/edit/',                  views.user_edit,               name='user_edit'),
    path('users/<uuid:uuid>/delete/',                views.user_delete,             name='user_delete'),
    path('users/<uuid:uuid>/restore/',               views.user_restore,            name='user_restore'),
    path('users/<uuid:uuid>/toggle-active/',         views.user_toggle_active,      name='user_toggle_active'),
    path('users/<uuid:uuid>/reset-password/',        views.user_reset_password,     name='user_reset_password'),

    # ─── Login History ────────────────────────────────────────────────────────────
    path('users/login-history/',                     views.login_history_list,      name='login_history_list'),

    # ─── User Activity ────────────────────────────────────────────────────────────
    path('users/activity/',                          views.user_activity_list,      name='user_activity_list'),

    # ─── Roles & Permissions ──────────────────────────────────────────────────────
    path('roles/',                                  views.role_list,                name='role_list'),
    path('roles/create/',                           views.role_create,              name='role_create'),
    path('roles/<int:pk>/delete/',                  views.role_delete,              name='role_delete'),
    path('roles/<str:token>/edit/',                 views.role_edit,                name='role_edit'),

    path('tracking/search/',                        views.staff_shipment_tracking,  name='staff_tracking'),
    path('tracking/updates/',                       views.tracking_updates,         name='tracking_updates'),
    path('tracking/history/',                       views.tracking_history,         name='tracking_history'),

    path('reports/shipments/',                      views.shipment_reports,         name='shipment_reports'),
    path('reports/delivery/',                       views.delivery_performance,     name='delivery_performance'),
    path('reports/revenue/',                        views.revenue_analytics,        name='revenue_analytics'),
    path('reports/customers/',                      views.customer_analytics,       name='customer_analytics'),
    path('reports/drivers/',                        views.driver_analytics,         name='driver_analytics'),
    path('reports/warehouse/',                      views.warehouse_analytics,      name='warehouse_analytics'),

    path('system/settings/',                        views.general_settings,         name='general_settings'),
    path('system/email/',                           views.email_config,             name='email_config'),
    path('system/audit-logs/',                      views.audit_logs,               name='audit_logs'),
    path('system/security/',                        views.security_settings,        name='security_settings'),
    path('system/backup/',                          views.backup_restore,           name='backup_restore'),
    path('system/activity-logs/',                   views.activity_logs,            name='activity_logs'),

    # Profile
    path('profile/',                                views.profile,                   name='profile'),
    path('profile/update/',                         views.profile_update,            name='profile_update'),
    path('profile/change-password/',                views.change_password,           name='change_password'),

    # Notifications
    path('notifications/',                          views.notifications_list,        name='notifications_list'),
    path('notifications/bell/',                     views.notifications_bell,        name='notifications_bell'),
    path('notifications/mark-all-read/',            views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('notifications/<int:pk>/read/',         views.notification_mark_read,    name='notification_mark_read'),

    # Support Tickets
    path('tickets/',                                views.ticket_list,               name='ticket_list'),
    path('tickets/create/',                         views.ticket_create,             name='ticket_create'),
    path('tickets/<str:token>/',                    views.ticket_detail,             name='ticket_detail'),

    # promo code
    path('promo-codes/',                            views.promo_code_list,           name='promo_code_list'),
    path('promo-codes/create/',                     views.promo_code_create,         name='promo_code_create'),
    path('promo-codes/<str:token>/edit/',           views.promo_code_edit,           name='promo_code_edit'),
    path('promo-codes/<str:token>/delete/',         views.promo_code_delete,         name='promo_code_delete'),

    path('orders/validate-promo/',                  views.validate_promo_code,       name='validate_promo_code'),
    path('quick-search/',                           views.quick_search,             name='quick_search'),

]