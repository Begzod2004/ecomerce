"""
Keyboards module for Telegram bot UI.
Contains keyboard layouts and button generators.
"""

from typing import List, Optional, Union
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from django.conf import settings
from ...models import Order
from .styles import Emojis

class KeyboardBuilder:
    """Builder class for creating keyboard layouts."""
    
    def __init__(self):
        self.buttons: List[List[InlineKeyboardButton]] = []
        self.current_row: List[InlineKeyboardButton] = []
        
    def add_button(self, text: str, callback_data: Optional[str] = None,
                  url: Optional[str] = None, web_app: Optional[WebAppInfo] = None) -> 'KeyboardBuilder':
        """Add button to current row."""
        button = InlineKeyboardButton(
            text=text,
            callback_data=callback_data,
            url=url,
            web_app=web_app
        )
        self.current_row.append(button)
        return self
        
    def row(self) -> 'KeyboardBuilder':
        """Complete current row and start new one."""
        if self.current_row:
            self.buttons.append(self.current_row)
            self.current_row = []
        return self
        
    def build(self) -> InlineKeyboardMarkup:
        """Build keyboard markup."""
        if self.current_row:
            self.buttons.append(self.current_row)
        return InlineKeyboardMarkup(self.buttons)

    @staticmethod
    def build_inline_keyboard(
        buttons: List[List[dict]],
        row_width: int = 2
    ) -> InlineKeyboardMarkup:
        """
        Build an inline keyboard from a list of button configurations.
        
        Args:
            buttons: List of button rows, each containing button configs with 'text' and 'callback_data'
            row_width: Number of buttons per row
            
        Returns:
            InlineKeyboardMarkup
        """
        keyboard = []
        current_row = []
        
        for row in buttons:
            row_buttons = []
            for button in row:
                if isinstance(button, dict):
                    btn = InlineKeyboardButton(
                        text=button.get('text', ''),
                        callback_data=button.get('callback_data'),
                        url=button.get('url'),
                    )
                    row_buttons.append(btn)
                elif isinstance(button, InlineKeyboardButton):
                    row_buttons.append(button)
            
            if row_buttons:
                keyboard.append(row_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_reply_keyboard(
        buttons: List[List[str]],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False
    ) -> ReplyKeyboardMarkup:
        """
        Build a reply keyboard from a list of button texts.
        
        Args:
            buttons: List of button rows, each containing button texts
            resize_keyboard: Whether to resize keyboard
            one_time_keyboard: Whether to hide keyboard after use
            
        Returns:
            ReplyKeyboardMarkup
        """
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                if isinstance(button, str):
                    keyboard_row.append(KeyboardButton(text=button))
                elif isinstance(button, dict):
                    keyboard_row.append(
                        KeyboardButton(
                            text=button.get('text', ''),
                            request_contact=button.get('request_contact', False),
                            request_location=button.get('request_location', False)
                        )
                    )
            keyboard.append(keyboard_row)
            
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard
        )

class Keyboards:
    """Keyboard layouts for different scenarios."""
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """Main menu keyboard with inline buttons."""
        builder = KeyboardBuilder()
        
        # Add web app button
        builder.add_button(
            f"{Emojis.STORE} Магазин",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        ).row()
        
        # Add orders button
        builder.add_button(
            f"{Emojis.ORDER} Мои заказы",
            callback_data="my_orders"
        ).row()
        
        # Add admin button if user is admin
        if is_admin:
            builder.add_button(
                f"{Emojis.ADMIN} Управление заказами",
                callback_data="manage_orders"
            ).row()
        
        return builder.build()
    
    @staticmethod
    def order_actions(order: Order) -> InlineKeyboardMarkup:
        """Order actions keyboard with inline buttons."""
        builder = KeyboardBuilder()
        
        # Add status-specific buttons
        if order.status == 'pending':
            builder.add_button(
                f"{Emojis.ACCEPT} Принять",
                callback_data=f"accept_order_{order.id}"
            ).add_button(
                f"{Emojis.ERROR} Отменить",
                callback_data=f"cancel_order_{order.id}"
            )
            
        elif order.status == 'processing':
            builder.add_button(
                f"{Emojis.SHIPPING} Отправить",
                callback_data=f"ship_order_{order.id}"
            )
            
        elif order.status == 'shipped':
            builder.add_button(
                f"{Emojis.SUCCESS} Доставлен",
                callback_data=f"deliver_order_{order.id}"
            )
        
        # Add refresh button
        builder.row().add_button(
            f"{Emojis.REFRESH} Обновить",
            callback_data=f"refresh_order_{order.id}"
        )
        
        # Add back button
        builder.row().add_button(
            f"{Emojis.BACK} Назад",
            callback_data="back_to_orders"
        )
            
        return builder.build()
    
    @staticmethod
    def orders_navigation(
        current_page: int,
        total_pages: int,
        filter_type: str = 'all'
    ) -> InlineKeyboardMarkup:
        """Navigation keyboard with inline buttons."""
        builder = KeyboardBuilder()
        
        # Add filter buttons
        builder.add_button(
            "Все заказы ✨" if filter_type == 'all' else "Все заказы",
            callback_data="filter_all"
        ).add_button(
            "Активные 🔥" if filter_type == 'active' else "Активные",
            callback_data="filter_active"
        ).row()
        
        # Add pagination
        if total_pages > 1:
            if current_page > 1:
                builder.add_button(
                    f"{Emojis.BACK}",
                    callback_data=f"page_{current_page-1}"
                )
                
            builder.add_button(
                f"{current_page}/{total_pages}",
                callback_data="current_page"
            )
            
            if current_page < total_pages:
                builder.add_button(
                    f"{Emojis.FORWARD}",
                    callback_data=f"page_{current_page+1}"
                )
                
            builder.row()
        
        # Add back button
        builder.add_button(f"{Emojis.BACK} Назад", callback_data="main_menu")
        
        return builder.build()
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard."""
        buttons = [
            [f"{Emojis.CART} Корзина", f"{Emojis.HEART} Избранное"],
            [f"{Emojis.SHOPPING} Каталог", f"{Emojis.PACKAGE} Мои заказы"],
            [f"{Emojis.INFO} Помощь", f"{Emojis.STORE} Наши магазины"]
        ]
        return KeyboardBuilder.build_reply_keyboard(buttons)
    
    @staticmethod
    def catalog_menu() -> ReplyKeyboardMarkup:
        """Catalog navigation keyboard."""
        buttons = [
            [f"{Emojis.SHOPPING} Все товары"],
            ["👕 Мужское", "👗 Женское"],
            ["👶 Детское", "🏃‍♂️ Спорт"],
            ["⬅️ Назад в меню"]
        ]
        return KeyboardBuilder.build_reply_keyboard(buttons)
    
    @staticmethod
    def order_actions(order_id: int) -> InlineKeyboardMarkup:
        """Order actions keyboard."""
        buttons = [
            [
                {
                    'text': f"{Emojis.INFO} Детали заказа",
                    'callback_data': f"order_details_{order_id}"
                }
            ],
            [
                {
                    'text': f"{Emojis.TRACKING} Отследить",
                    'callback_data': f"track_order_{order_id}"
                },
                {
                    'text': f"{Emojis.CANCELED} Отменить",
                    'callback_data': f"cancel_order_{order_id}"
                }
            ]
        ]
        return KeyboardBuilder.build_inline_keyboard(buttons)
    
    @staticmethod
    def product_actions(product_id: int) -> InlineKeyboardMarkup:
        """Product actions keyboard."""
        buttons = [
            [
                {
                    'text': f"{Emojis.CART} Добавить в корзину",
                    'callback_data': f"add_to_cart_{product_id}"
                }
            ],
            [
                {
                    'text': f"{Emojis.HEART} В избранное",
                    'callback_data': f"add_to_wishlist_{product_id}"
                },
                {
                    'text': f"{Emojis.INFO} Подробнее",
                    'callback_data': f"product_details_{product_id}"
                }
            ]
        ]
        return KeyboardBuilder.build_inline_keyboard(buttons)
    
    @staticmethod
    def confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
        """Generic confirmation keyboard."""
        buttons = [
            [
                {
                    'text': f"{Emojis.SUCCESS} Да",
                    'callback_data': f"confirm_{action}_{item_id}"
                },
                {
                    'text': f"{Emojis.CANCELED} Нет",
                    'callback_data': f"cancel_{action}_{item_id}"
                }
            ]
        ]
        return KeyboardBuilder.build_inline_keyboard(buttons)
    
    @staticmethod
    def back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
        """Single back button keyboard."""
        buttons = [
            [
                {
                    'text': "⬅️ Назад",
                    'callback_data': callback_data
                }
            ]
        ]
        return KeyboardBuilder.build_inline_keyboard(buttons) 