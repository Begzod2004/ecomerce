"""
User service module for Telegram bot.
Contains business logic for user management.
"""

import logging
from typing import Optional, Tuple, List
from django.db.models import Q
from asgiref.sync import sync_to_async
from django.conf import settings
from ...models import User
from ..ui.messages import MessageTemplates

logger = logging.getLogger(__name__)

class UserService:
    """Service for handling user-related operations."""
    
    @staticmethod
    @sync_to_async
    def get_or_create_user(
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None
    ) -> Tuple[User, bool]:
        """Get or create user by Telegram ID."""
        try:
            # Try to get existing user
            user = User.objects.filter(telegram_id=str(telegram_id)).first()
            
            if user:
                # Update user info if needed
                updated = False
                if username and user.telegram_username != username:
                    user.telegram_username = username
                    updated = True
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
                    
                if updated:
                    user.save()
                    logger.info(f"Updated user {telegram_id} info")
                    
                return user, False
            
            # Create new user
            user = User.objects.create(
                telegram_id=str(telegram_id),
                telegram_username=username,
                username=username or f"user_{telegram_id}",
                first_name=first_name or "",
                last_name=last_name or "",
                is_telegram_user=True,
                is_telegram_admin=str(telegram_id) in map(str, settings.TELEGRAM_ADMIN_USER_IDS)
            )
            
            logger.info(f"Created new user {telegram_id}")
            return user, True
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {str(e)}")
            return None, False
    
    @staticmethod
    @sync_to_async
    def get_user(telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        try:
            return User.objects.filter(telegram_id=str(telegram_id)).first()
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def update_user(user: User, **data) -> Optional[User]:
        """Update user data."""
        try:
            for key, value in data.items():
                setattr(user, key, value)
            user.save()
            logger.info(f"Updated user {user.telegram_id} data")
            return user
        except Exception as e:
            logger.error(f"Error updating user {user.telegram_id}: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def get_admin_users() -> List[User]:
        """Get all admin users."""
        try:
            return list(User.objects.filter(is_telegram_admin=True))
        except Exception as e:
            logger.error(f"Error getting admin users: {str(e)}")
            return []
    
    @staticmethod
    @sync_to_async
    def search_users(query: str) -> List[User]:
        """Search users by various fields."""
        try:
            return list(User.objects.filter(
                Q(telegram_username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(telegram_id__icontains=query)
            ))
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []
    
    @staticmethod
    @sync_to_async
    def set_user_admin_status(telegram_id: int, is_admin: bool) -> Optional[User]:
        """Set user admin status."""
        try:
            user = User.objects.filter(telegram_id=str(telegram_id)).first()
            if not user:
                return None
                
            user.is_telegram_admin = is_admin
            user.save()
            
            action = "added to" if is_admin else "removed from"
            logger.info(f"User {telegram_id} {action} admin list")
            
            return user
            
        except Exception as e:
            logger.error(f"Error setting admin status for user {telegram_id}: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def validate_user_action(user: User, action: str) -> Tuple[bool, str]:
        """Validate if user action is allowed."""
        try:
            if not user:
                return False, "Пользователь не найден"
                
            if action == "make_admin":
                if user.is_telegram_admin:
                    return False, "Пользователь уже является администратором"
                    
            elif action == "remove_admin":
                if not user.is_telegram_admin:
                    return False, "Пользователь не является администратором"
                    
            elif action == "block":
                if not user.is_active:
                    return False, "Пользователь уже заблокирован"
                    
            elif action == "unblock":
                if user.is_active:
                    return False, "Пользователь не заблокирован"
                    
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error validating user action: {str(e)}")
            return False, "Произошла ошибка при проверке"
    
    @staticmethod
    @sync_to_async
    def block_user(telegram_id: int) -> Optional[User]:
        """Block user."""
        try:
            user = User.objects.filter(telegram_id=str(telegram_id)).first()
            if not user:
                return None
                
            user.is_active = False
            user.save()
            
            logger.info(f"Blocked user {telegram_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error blocking user {telegram_id}: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def unblock_user(telegram_id: int) -> Optional[User]:
        """Unblock user."""
        try:
            user = User.objects.filter(telegram_id=str(telegram_id)).first()
            if not user:
                return None
                
            user.is_active = True
            user.save()
            
            logger.info(f"Unblocked user {telegram_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error unblocking user {telegram_id}: {str(e)}")
            return None
    
    @staticmethod
    @sync_to_async
    def get_user_stats() -> dict:
        """Get user statistics."""
        try:
            stats = {
                'total': User.objects.count(),
                'admins': User.objects.filter(is_telegram_admin=True).count(),
                'active': User.objects.filter(is_active=True).count(),
                'blocked': User.objects.filter(is_active=False).count(),
                'with_orders': User.objects.filter(orders__isnull=False).distinct().count(),
                'today': User.objects.filter(date_joined__date=timezone.now().date()).count()
            }
            
            # Calculate percentages
            total = stats['total'] or 1  # Avoid division by zero
            stats.update({
                'admins_percent': round(stats['admins'] / total * 100, 1),
                'active_percent': round(stats['active'] / total * 100, 1),
                'blocked_percent': round(stats['blocked'] / total * 100, 1),
                'with_orders_percent': round(stats['with_orders'] / total * 100, 1)
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                'total': 0,
                'admins': 0,
                'active': 0,
                'blocked': 0,
                'with_orders': 0,
                'today': 0,
                'admins_percent': 0,
                'active_percent': 0,
                'blocked_percent': 0,
                'with_orders_percent': 0
            } 