"""
Styles module for Telegram bot UI.
Contains emojis and text styles.
"""

class Colors:
    PRIMARY = '#7B1FA2'  # Deep Purple
    SECONDARY = '#9C27B0'  # Purple
    SUCCESS = '#4CAF50'  # Green
    WARNING = '#FFC107'  # Amber
    DANGER = '#F44336'  # Red
    INFO = '#2196F3'  # Blue
    LIGHT = '#F5F5F5'  # Light Grey
    DARK = '#212121'  # Dark Grey
    WHITE = '#FFFFFF'  # White
    BLACK = '#000000'  # Black

class Emojis:
    """Emoji constants for UI elements."""
    
    # Status emojis
    PENDING = "⏳"
    PROCESSING = "🔄"
    READY = "✨"
    SHIPPED = "📦"
    DELIVERED = "✅"
    CANCELED = "❌"
    RETURNED = "↩️"
    
    # General emojis
    NOTIFICATION = "🔔"
    STATUS = "📍"
    PRICE = "💰"
    BRANCH = "🏪"
    HOME = "🏠"
    WELCOME = "👋"
    SHOPPING = "🛍️"
    STAR = "⭐"
    HEART = "❤️"
    CART = "🛒"
    GIFT = "🎁"
    MONEY = "💵"
    CALENDAR = "📅"
    CLOCK = "⏰"
    PHONE = "📱"
    EMAIL = "📧"
    LINK = "🔗"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    SUCCESS = "✅"
    
    # UI elements
    STORE = "🏪"
    ADMIN = "👨‍💼"
    LOCATION = "📍"
    PACKAGE = "📦"
    TRACKING = "🔍"
    
    # Navigation
    BACK = "⬅️"
    FORWARD = "➡️"
    REFRESH = "🔄"
    ACCEPT = "✅"

class TextStyles:
    """Text formatting styles."""
    
    # Markdown styles
    BOLD = "*{}*"
    ITALIC = "_{}_"
    CODE = "`{}`"
    STRIKE = "~{}~"
    UNDERLINE = "__{}__"
    
    # Custom styles
    HEADER = "*{}*\n"
    SUBHEADER = "_{}:_\n"
    LIST_ITEM = "• {}"
    NUMBERED_ITEM = "{}. {}"
    SECTION = "\n{}\n"
    DIVIDER = "\n---\n"
    
    @staticmethod
    def bold(text: str) -> str:
        """Make text bold."""
        return TextStyles.BOLD.format(text)
        
    @staticmethod
    def italic(text: str) -> str:
        """Make text italic."""
        return TextStyles.ITALIC.format(text)
        
    @staticmethod
    def code(text: str) -> str:
        """Format text as code."""
        return TextStyles.CODE.format(text)
        
    @staticmethod
    def strike(text: str) -> str:
        """Format text as strikethrough."""
        return TextStyles.STRIKE.format(text)
        
    @staticmethod
    def underline(text: str) -> str:
        """Format text as underlined."""
        return TextStyles.UNDERLINE.format(text)
        
    @staticmethod
    def header(text: str) -> str:
        """Format section title."""
        return TextStyles.HEADER.format(text)
        
    @staticmethod
    def subheader(text: str) -> str:
        """Format subheader."""
        return TextStyles.SUBHEADER.format(text)
        
    @staticmethod
    def list_item(text: str) -> str:
        """Format list item."""
        return TextStyles.LIST_ITEM.format(text)
        
    @staticmethod
    def numbered_item(number: int, text: str) -> str:
        """Format numbered item."""
        return TextStyles.NUMBERED_ITEM.format(number, text)
        
    @staticmethod
    def section(text: str) -> str:
        """Format section."""
        return TextStyles.SECTION.format(text)
        
    @staticmethod
    def link(text: str, url: str) -> str:
        """Create markdown link."""
        return f"[{text}]({url})"
        
    @staticmethod
    def key_value(key: str, value: str, emoji: str = "") -> str:
        """Format key-value pair."""
        emoji_prefix = f"{emoji} " if emoji else ""
        return f"{emoji_prefix}{key}: {value}\n"
        
    @staticmethod
    def price(amount: float, currency: str = "сум") -> str:
        """Format price."""
        return f"{amount:,.0f} {currency}"
        
    @staticmethod
    def divider(char: str = "—", length: int = 32) -> str:
        """Create text divider."""
        return f"\n{char * length}\n" 