"""
Order service module for Telegram bot.
Contains business logic for order management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async
from ...models import Order, User
from ..ui.messages import OrderMessages

logger = logging.getLogger(__name__)

class OrderService:
    """Service for handling order-related operations."""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    @sync_to_async
    def get_user_orders(user: User) -> List[Order]:
        """Get all orders for a user."""
        try:
            cache_key = f'user_orders_{user.id}'
            cached_orders = cache.get(cache_key)
            
            if cached_orders is not None:
                return cached_orders
            
            orders = list(Order.objects.filter(user=user).select_related(
                'user',
                'shipping_method',
                'branch',
            ).prefetch_related(
                'items__product',
                'items__variant',
                'items__variant__color',
                'items__variant__size',
                'items__product__brand',
            ).order_by('-created_at'))
            
            cache.set(cache_key, orders, OrderService.CACHE_TIMEOUT)
            return orders
            
        except Exception as e:
            logger.error(f"Error getting user orders: {str(e)}")
            return []
    
    @staticmethod
    @sync_to_async
    def get_active_orders() -> List[Order]:
        """Get all active orders."""
        try:
            cache_key = 'active_orders'
            cached_orders = cache.get(cache_key)
            
            if cached_orders is not None:
                return cached_orders
            
            orders = list(Order.objects.exclude(
                status__in=['delivered', 'canceled', 'returned']
            ).select_related(
                'user',
                'shipping_method',
                'branch',
            ).prefetch_related(
                'items__product',
                'items__variant',
                'items__variant__color',
                'items__variant__size',
                'items__product__brand',
            ).order_by('-created_at'))
            
            cache.set(cache_key, orders, OrderService.CACHE_TIMEOUT)
            return orders
            
        except Exception as e:
            logger.error(f"Error getting active orders: {str(e)}")
            return []
    
    @staticmethod
    @sync_to_async
    def get_order_by_id(order_id: int) -> Optional[Order]:
        """Get order by ID."""
        try:
            cache_key = f'order_{order_id}'
            cached_order = cache.get(cache_key)
            
            if cached_order is not None:
                return cached_order
            
            order = Order.objects.select_related(
                'user',
                'shipping_method',
                'branch',
            ).prefetch_related(
                'items__product',
                'items__variant',
                'items__variant__color',
                'items__variant__size',
                'items__product__brand',
            ).get(id=order_id)
            
            cache.set(cache_key, order, OrderService.CACHE_TIMEOUT)
            return order
            
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def update_order_status(order_id: int, new_status: str) -> Optional[Order]:
        """Update order status."""
        try:
            order = Order.objects.select_related(
                'user',
                'shipping_method',
                'branch',
            ).prefetch_related(
                'items__product',
                'items__variant',
                'items__variant__color',
                'items__variant__size',
                'items__product__brand',
            ).get(id=order_id)
            
            order.status = new_status
            order.save()
            
            # Clear cache
            cache.delete(f'order_{order_id}')
            cache.delete(f'user_orders_{order.user.id}')
            cache.delete('active_orders')
            
            logger.info(f"Updated order {order_id} status to {new_status}")
            return order
            
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def get_filtered_orders(
        filter_type: str = 'all',
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Order], int]:
        """Get filtered and paginated orders."""
        try:
            cache_key = f'filtered_orders_{filter_type}_{page}'
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Base queryset with all needed relations
            queryset = Order.objects.select_related(
                'user',
                'shipping_method',
                'branch',
            ).prefetch_related(
                'items__product',
                'items__variant',
                'items__variant__color',
                'items__variant__size',
                'items__product__brand',
            )
            
            # Apply filters
            if filter_type == 'active':
                queryset = queryset.exclude(status__in=['delivered', 'canceled', 'returned'])
            elif filter_type != 'all':
                queryset = queryset.filter(status=filter_type)
            
            # Calculate total pages
            total_orders = queryset.count()
            total_pages = (total_orders + page_size - 1) // page_size
            
            # Get paginated results
            start = (page - 1) * page_size
            end = start + page_size
            orders = list(queryset.order_by('-created_at')[start:end])
            
            result = (orders, total_pages)
            cache.set(cache_key, result, OrderService.CACHE_TIMEOUT)
            return result
            
        except Exception as e:
            logger.error(f"Error getting filtered orders: {str(e)}")
            return [], 0
    
    @staticmethod
    async def format_order_message(order: Order, show_items: bool = True) -> str:
        """Format order message using OrderMessages."""
        return OrderMessages.format_order_details(order, show_items)
    
    @staticmethod
    async def format_order_list(orders: List[Order]) -> str:
        """Format order list message using OrderMessages."""
        return OrderMessages.format_order_list(orders)
    
    @staticmethod
    async def format_order_status_update(order: Order) -> str:
        """Format order status update message using OrderMessages."""
        return OrderMessages.format_order_status_update(order)
    
    @staticmethod
    @sync_to_async
    def validate_order_action(order_id: int, action: str, user: User) -> Tuple[bool, str]:
        """Validate if order action is allowed."""
        try:
            order = Order.objects.get(id=order_id)
            
            # Check if order exists
            if not order:
                return False, "Заказ не найден"
            
            # Check if user has permission
            if not user.is_telegram_admin:
                return False, "У вас нет прав для этого действия"
            
            # Validate status transitions
            valid_transitions = {
                'pending': ['processing', 'canceled'],
                'processing': ['shipped', 'canceled'],
                'shipped': ['delivered', 'returned'],
                'delivered': ['returned'],
                'canceled': [],
                'returned': []
            }
            
            if action not in valid_transitions.get(order.status, []):
                return False, f"Невозможно изменить статус с {order.status} на {action}"
            
            return True, "OK"
            
        except Order.DoesNotExist:
            return False, "Заказ не найден"
        except Exception as e:
            logger.error(f"Error validating order action: {str(e)}")
            return False, "Произошла ошибка при проверке" 