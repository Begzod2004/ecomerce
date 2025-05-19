from django.urls import reverse
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from unfold.dashboards import Dashboard
from unfold.dashboards.modules import LinkList, ModelList, Group, ChartJs, Stats
from .models import User, Product, Order, OrderItem, Category, ProductReview

# Instead of building a dashboard function, we'll create a dashboard class
class AdminDashboard(Dashboard):
    name = "e-commerce-dashboard"
    title = "E-commerce Dashboard"

    def init_with_context(self, context):
        """Initialize the dashboard with components"""
        # Get time ranges for statistics
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        try:
            # Sales statistics
            recent_orders = Order.objects.filter(created_at__date__gte=last_month)
            today_sales = recent_orders.filter(created_at__date=today).aggregate(Sum('final_amount'))['final_amount__sum'] or 0
            yesterday_sales = recent_orders.filter(created_at__date=yesterday).aggregate(Sum('final_amount'))['final_amount__sum'] or 0
            weekly_sales = recent_orders.filter(created_at__date__gte=last_week).aggregate(Sum('final_amount'))['final_amount__sum'] or 0
            monthly_sales = recent_orders.aggregate(Sum('final_amount'))['final_amount__sum'] or 0

            # Orders statistics
            pending_orders = Order.objects.filter(status='pending').count()
            processing_orders = Order.objects.filter(status='processing').count()
            shipped_orders = Order.objects.filter(status='shipped').count()
            delivered_orders = Order.objects.filter(status='delivered').count()
            
            # Product statistics
            low_stock_products = Product.objects.filter(stock__lte=5).count()
            out_of_stock = Product.objects.filter(stock=0).count()
            
            # Customer statistics
            total_customers = User.objects.count()
            new_customers = User.objects.filter(created_at__date__gte=last_month).count()
            
            # Add Stats widgets
            self.append(
                Stats(
                    title="Sales Overview",
                    entries=[
                        {"title": "Today's Sales", "value": f"${today_sales}", "icon": "attach_money"},
                        {"title": "Yesterday's Sales", "value": f"${yesterday_sales}", "icon": "attach_money"},
                        {"title": "Weekly Sales", "value": f"${weekly_sales}", "icon": "attach_money"},
                        {"title": "Monthly Sales", "value": f"${monthly_sales}", "icon": "attach_money"},
                    ],
                )
            )
            
            self.append(
                Stats(
                    title="Order Status",
                    entries=[
                        {"title": "Pending Orders", "value": pending_orders, "icon": "pending"},
                        {"title": "Processing Orders", "value": processing_orders, "icon": "loop"},
                        {"title": "Shipped Orders", "value": shipped_orders, "icon": "local_shipping"},
                        {"title": "Delivered Orders", "value": delivered_orders, "icon": "check_circle"},
                    ],
                )
            )
            
            self.append(
                Stats(
                    title="Inventory Summary",
                    entries=[
                        {"title": "Low Stock Products", "value": low_stock_products, "icon": "warning"},
                        {"title": "Out of Stock Products", "value": out_of_stock, "icon": "error"},
                        {"title": "Total Customers", "value": total_customers, "icon": "people"},
                        {"title": "New Customers (30 days)", "value": new_customers, "icon": "person_add"},
                    ],
                )
            )
            
            # Add quick links
            self.append(
                LinkList(
                    title="Quick Actions",
                    entries=[
                        {"title": "Add New Product", "url": reverse("admin:unicflo_api_product_add")},
                        {"title": "Add New Category", "url": reverse("admin:unicflo_api_category_add")},
                        {"title": "View All Orders", "url": reverse("admin:unicflo_api_order_changelist")},
                        {"title": "Add New Coupon", "url": reverse("admin:unicflo_api_coupon_add")},
                    ],
                )
            )
            
            # Add model list for recent products and orders
            self.append(
                Group(
                    title="Recent Items",
                    module_list=[
                        ModelList(
                            title="Recent Products",
                            models=["unicflo_api.product"],
                            limit=5,
                        ),
                        ModelList(
                            title="Recent Orders",
                            models=["unicflo_api.order"],
                            limit=5,
                        ),
                    ],
                )
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating dashboard data: {str(e)}")
            
            # Add a simple link list in case of error
            self.append(
                LinkList(
                    title="Navigation",
                    entries=[
                        {"title": "Products", "url": reverse("admin:unicflo_api_product_changelist")},
                        {"title": "Orders", "url": reverse("admin:unicflo_api_order_changelist")},
                        {"title": "Users", "url": reverse("admin:unicflo_api_user_changelist")},
                    ],
                )
            )  