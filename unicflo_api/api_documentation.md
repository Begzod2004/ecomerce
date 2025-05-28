# UnicFlo API Dokumentatsiyasi

## Loyiha Haqida Umumiy Ma'lumot

UnicFlo API elektron tijorat tizimining backend qismi bo'lib, Django Rest Framework asosida yaratilgan. Bu API mobil ilova va veb saytlar bilan integratsiya uchun RESTful endpointlar to'plamini taqdim etadi.

## API Arxitekturasi

UnicFlo API quyidagi asosiy komponentlardan iborat:

1. **Modellar** - Ma'lumotlar bazasi sxemasi
2. **Serializerlar** - Ma'lumotlarni formatlash va validatsiya
3. **Viewlar** - API endpointlari logikasi
4. **URLlar** - Routing va endpointlar
5. **Autentifikatsiya** - Telegram ID orqali
6. **Permissionlar** - Foydalanuvchi huquqlari
7. **Pagination** - Sahifalash
8. **Filters** - Ma'lumotlarni filtrlash

## Asosiy Endpointlar

| Endpoint                     | Method             | Tavsif                                |
| ---------------------------- | ------------------ | ------------------------------------- |
| `/users/`                    | GET, POST          | Foydalanuvchilar ro'yxati va yaratish |
| `/users/me/`                 | GET, PUT, PATCH    | Joriy foydalanuvchi ma'lumotlari      |
| `/categories/`               | GET                | Kategoriyalar ro'yxati                |
| `/subcategories/`            | GET                | Subkategoriyalar ro'yxati             |
| `/products/`                 | GET                | Mahsulotlar ro'yxati                  |
| `/products/<slug>/`          | GET                | Mahsulot tafsilotlari                 |
| `/products/direct-purchase/` | POST               | To'g'ridan-to'g'ri sotib olish        |
| `/cart/`                     | GET                | Savatcha ma'lumotlari                 |
| `/cart/add/`                 | POST               | Savatchaga qo'shish                   |
| `/orders/`                   | GET, POST          | Buyurtmalar ro'yxati va yaratish      |
| `/orders/<id>/`              | GET, PATCH, DELETE | Buyurtma tafsilotlari                 |
| `/branches/`                 | GET                | Filiallar ro'yxati                    |

## Asosiy Modellar

### 1. User (Foydalanuvchi)

```python
class User(AbstractUser):
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    is_telegram_user = models.BooleanField(default=False)
    is_telegram_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    # ...
```

### 2. Product (Mahsulot)

```python
class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    gender = models.ForeignKey(GenderCategory, on_delete=models.SET_NULL, null=True, blank=True)
    # ...
```

### 3. Cart (Savatcha)

```python
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    promo_code_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # ...
```

### 4. Order (Buyurtma)

```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('processing', 'Qayta ishlanmoqda'),
        ('shipped', 'Yuborilgan'),
        ('delivered', 'Yetkazib berilgan'),
        ('canceled', 'Bekor qilingan')
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Yetkazib berilganda to\'lov'),
        ('cash_on_pickup', 'Olib ketishda to\'lov'),
        ('card', 'Karta orqali to\'lov'),
        ('split', 'Bo\'lib to\'lash')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup_branch = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True, blank=True)
    # ...

    # Split payment fields
    is_split_payment = models.BooleanField(default=False)
    first_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    first_payment_date = models.DateTimeField(null=True, blank=True)
    second_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    second_payment_due_date = models.DateTimeField(null=True, blank=True)
    second_payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # ...
```

### 5. Address (Filial)

```python
class Address(models.Model):
    name = models.CharField(max_length=100)
    branch_type = models.CharField(max_length=20, choices=[
        ('store', 'Do\'kon'),
        ('pickup', 'Olib ketish punkti'),
        ('warehouse', 'Ombor')
    ])
    street = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    # ...
```

## Autentifikatsiya

UnicFlo API foydalanuvchilarni Telegram ID orqali autentifikatsiya qiladi.

```python
class TelegramAuthMixin:
    """
    Base mixin for Telegram authentication.
    """
    def get_user_from_telegram_id(self):
        telegram_id = self.request.META.get('HTTP_X_TELEGRAM_ID')
        if not telegram_id:
            raise exceptions.AuthenticationFailed({
                'error': 'Authentication failed',
                'message': 'X-Telegram-ID header is required',
                'status': 401
            })
        # ...
```

## API Endpoints

### 1. Foydalanuvchi API

#### Foydalanuvchi ma'lumotlarini olish

**URL**: `/users/me/`  
**Method**: `GET`  
**Headers**: `X-Telegram-ID: <telegram_id>`

```python
class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
```

**Javob (200 OK)**:

```json
{
  "id": 1,
  "username": "user123",
  "telegram_id": "123456789",
  "telegram_username": "username",
  "first_name": "John",
  "last_name": "Doe",
  "is_telegram_user": true,
  "is_telegram_admin": false,
  "is_verified": true
}
```

### 2. Mahsulotlar API

#### Mahsulotlar ro'yxatini olish

**URL**: `/products/`  
**Method**: `GET`  
**Query Parameters**: `category`, `subcategory`, `brand`, `price_min`, `price_max`, `has_discount`, `search`, ...

```python
class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    # ...
```

**Javob (200 OK)**:

```json
{
  "count": 100,
  "next": "/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Mahsulot nomi",
      "slug": "mahsulot-nomi",
      "description": "Mahsulot tavsifi",
      "price": 150000.0,
      "discount_price": 120000.0,
      "images": [
        {
          "id": 1,
          "image": "/media/products/image1.jpg",
          "is_primary": true
        }
      ],
      "variants": [
        {
          "id": 1,
          "color_name": "Qora",
          "color_hex": "#000000",
          "size_name": "M",
          "stock": 10
        }
      ]
    }
  ]
}
```

### 3. Savatcha API

#### Savatchaga mahsulot qo'shish

**URL**: `/cart/add/`  
**Method**: `POST`  
**Headers**: `X-Telegram-ID: <telegram_id>`

```python
class AddToCartView(TelegramAuthMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get user from request context
        user = self.get_user_from_telegram_id()

        # Get active cart for user
        cart = Cart.objects.filter(user=user, is_active=True).first()
        if not cart:
            # Create new cart if not exists
            cart = Cart.objects.create(user=user, is_active=True)
        # ...
```

**So'rov Body**:

```json
{
  "product_id": 1,
  "variant_id": 1,
  "quantity": 2
}
```

**Javob (201 Created)**:

```json
{
  "message": "Product added to cart successfully",
  "cart_item": {
    "id": 1,
    "product": 1,
    "product_name": "Mahsulot nomi",
    "quantity": 2,
    "total_price": 240000.0
  }
}
```

### 4. Buyurtma API

#### Buyurtma yaratish

**URL**: `/orders/`  
**Method**: `POST`  
**Headers**: `X-Telegram-ID: <telegram_id>`

```python
class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    # ...

    def perform_create(self, serializer):
        serializer.save()
```

**So'rov Body**:

```json
{
  "cart_id": 1,
  "pickup_branch_id": 2,
  "customer_name": "John Doe",
  "phone_number": "+998901234567",
  "payment_method": "cash_on_pickup",
  "order_note": "Qo'shimcha ma'lumot",
  "is_split_payment": false
}
```

**Javob (201 Created)**:

```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "user123"
  },
  "total_amount": 240000.0,
  "discount_amount": 0.0,
  "shipping_amount": 0.0,
  "final_amount": 240000.0,
  "status": "pending",
  "payment_method": "cash_on_pickup",
  "customer_name": "John Doe",
  "phone_number": "+998901234567"
}
```

### 5. To'g'ridan-to'g'ri Sotib Olish API

#### Mahsulotni to'g'ridan-to'g'ri sotib olish

**URL**: `/products/direct-purchase/`  
**Method**: `POST`  
**Headers**: `X-Telegram-ID: <telegram_id>`

```python
class DirectPurchaseView(TelegramAuthMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DirectPurchaseSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Get user from telegram ID
                    user = self.get_user_from_telegram_id()

                    # Get validated data
                    data = serializer.validated_data
                    product = Product.objects.get(id=data['product_id'])
                    pickup_branch = Address.objects.get(id=data['pickup_branch_id'])

                    # Create order
                    order = Order.objects.create(
                        user=user,
                        pickup_branch=pickup_branch,
                        customer_name=data['customer_name'],
                        phone_number=data['phone_number'],
                        payment_method=data['payment_method'],
                        order_note=data.get('order_note', ''),
                        is_split_payment=data.get('is_split_payment', False),
                        status='pending'
                    )
                    # ...
```

**So'rov Body**:

```json
{
  "product_id": 1,
  "variant_id": 1,
  "quantity": 1,
  "pickup_branch_id": 2,
  "payment_method": "cash_on_pickup",
  "customer_name": "John Doe",
  "phone_number": "+998901234567",
  "order_note": "Qo'shimcha ma'lumot",
  "is_split_payment": false
}
```

**Javob (201 Created)**:

```json
{
  "message": "Buyurtma muvaffaqiyatli yaratildi",
  "order": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "user123"
    },
    "total_amount": 120000.0,
    "discount_amount": 0.0,
    "shipping_amount": 0.0,
    "final_amount": 120000.0,
    "status": "pending",
    "payment_method": "cash_on_pickup",
    "customer_name": "John Doe",
    "phone_number": "+998901234567"
  }
}
```

### 6. Filiallar API

#### Filiallar ro'yxatini olish

**URL**: `/branches/`  
**Method**: `GET`  
**Headers**: `X-Telegram-ID: <telegram_id>` (ixtiyoriy)

```python
class ActiveBranchesView(TelegramAuthMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branches = Address.objects.filter(
            branch_type__in=['store', 'pickup'],
            is_active=True
        ).order_by('name')

        serializer = AddressSerializer(branches, many=True)
        return Response(serializer.data)
```

**Javob (200 OK)**:

```json
[
  {
    "id": 1,
    "name": "Chilonzor Do'koni",
    "branch_type": "store",
    "street": "Chilonzor 9-kvartal",
    "city": "Toshkent",
    "phone": "+998712345678",
    "working_hours": "09:00-20:00",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Yunusobod Pickup Punkti",
    "branch_type": "pickup",
    "street": "Amir Temur shoh ko'chasi, 108",
    "city": "Toshkent",
    "phone": "+998712345678",
    "working_hours": "10:00-22:00",
    "is_active": true
  }
]
```

## Bo'lib To'lash Mexanizmi

UnicFlo API bo'lib to'lash funksiyasini qo'llab-quvvatlaydi. Bu mexanizm buyurtmani ikki bosqichda to'lashga imkon beradi.

```python
def calculate_totals(self):
    """Calculate order totals including split payment amounts"""
    # Calculate total from items
    items_total = sum(item.total_price for item in self.items.all())

    # Apply discount
    self.total_amount = items_total
    self.discount_amount = 0  # Calculate discount if needed

    # Apply shipping cost
    self.shipping_amount = 0  # Calculate shipping if needed

    # Calculate final amount
    self.final_amount = self.total_amount - self.discount_amount + self.shipping_amount

    # Handle split payment
    if self.is_split_payment:
        # 50% for first payment, 50% for second payment
        self.first_payment_amount = self.final_amount / 2
        self.second_payment_amount = self.final_amount / 2

        # Set payment dates
        self.first_payment_date = timezone.now()
        self.second_payment_due_date = timezone.now() + timedelta(days=30)

        # Set payment statuses
        self.payment_status = 'pending'
        self.second_payment_status = 'pending'
    else:
        # Reset split payment fields
        self.first_payment_amount = None
        self.first_payment_date = None
        self.second_payment_amount = None
        self.second_payment_due_date = None
        self.second_payment_status = 'pending'

    self.save()
```

## Frontend bilan Integratsiya

### Mahsulotlar ro'yxatini olish

```javascript
async function fetchProducts(filters = {}) {
  try {
    let queryParams = new URLSearchParams();

    // Add filters to query params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        queryParams.append(key, value);
      }
    });

    const response = await fetch(`/products/?${queryParams.toString()}`, {
      method: "GET",
      headers: {
        "X-Telegram-ID": "123456789", // Foydalanuvchining Telegram ID
      },
    });

    if (response.ok) {
      const data = await response.json();
      return data;
    } else {
      throw new Error("Mahsulotlarni yuklashda xatolik");
    }
  } catch (error) {
    console.error("Error fetching products:", error);
    throw error;
  }
}
```

### To'g'ridan-to'g'ri Sotib Olish

```javascript
async function directPurchase(productData) {
  try {
    const response = await fetch("/products/direct-purchase/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-ID": "123456789", // Foydalanuvchining Telegram ID
      },
      body: JSON.stringify({
        product_id: productData.id,
        variant_id: productData.selectedVariant?.id,
        quantity: productData.quantity,
        pickup_branch_id: productData.selectedBranch.id,
        payment_method: productData.paymentMethod,
        customer_name: productData.customerName,
        phone_number: productData.phoneNumber,
        order_note: productData.note,
        is_split_payment: productData.isSplitPayment,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      // Muvaffaqiyatli
      return data;
    } else {
      // Xatolik
      throw new Error(data.message || "Sotib olishda xatolik");
    }
  } catch (error) {
    console.error("Error during purchase:", error);
    throw error;
  }
}
```

## Tavsiyalar

1. **Headerlarga e'tibor bering**: Barcha so'rovlarda `X-Telegram-ID` headerini qo'shish kerak.
2. **Xatoliklar bilan ishlash**: Har bir so'rovdan keyin `response.ok` tekshirilishi kerak.
3. **Keshlashtirish**: Filiallar ro'yxati kabi kam o'zgaradigan ma'lumotlarni keshlab saqlash tavsiya etiladi.
4. **Versiyalash**: API o'zgartirilganda versiyalash mexanizmlaridan foydalanish kerak.

## Xulosa

UnicFlo API keng qamrovli funksionallikni ta'minlaydi, shu jumladan:

1. **Mahsulotlar boshqaruvi** - mahsulotlar ro'yxati, qidirish, filtrlash
2. **Savatcha boshqaruvi** - mahsulotlarni qo'shish, miqdorini o'zgartirish, o'chirish
3. **Buyurtmalar boshqaruvi** - buyurtma yaratish, holati o'zgartirish, bekor qilish
4. **To'g'ridan-to'g'ri sotib olish** - savatchasiz tezkor xarid
5. **Bo'lib to'lash** - buyurtmani ikki bosqichda to'lash
6. **Filiallar boshqaruvi** - filiallar ro'yxati, ma'lumotlari

Bu API mobil ilova va veb saytlar bilan integratsiya uchun optimal interfeysni ta'minlaydi.
