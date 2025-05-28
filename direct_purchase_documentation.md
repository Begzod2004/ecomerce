# UnicFlo API: To'g'ridan-to'g'ri Sotib Olish va Filiallar API Dokumentatsiyasi

## Loyiha Haqida Umumiy Ma'lumot

UnicFlo API elektron tijorat tizimining backend qismi bo'lib, Django Rest Framework asosida yaratilgan. Bu dokumentatsiya to'g'ridan-to'g'ri sotib olish (Direct Purchase) va filiallar (Branches) API endpointlari haqida batafsil ma'lumot beradi.

## Ma'lumotlar Modeli

### Address (Filial) Modeli

Filiallar `Address` modeli orqali boshqariladi. Filiallar manzil va ma'lumotlarni saqlash uchun xizmat qiladi.

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
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Uzbekistan')
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20)
    working_hours = models.CharField(max_length=100, default='09:00-18:00')
    is_active = models.BooleanField(default=True)
    location_link = models.URLField(blank=True, null=True)
    manager_name = models.CharField(max_length=100, blank=True, null=True)
    manager_phone = models.CharField(max_length=20, blank=True, null=True)
    has_fitting_room = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    is_24_hours = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Order Modeli

Buyurtmalar `Order` modeli orqali boshqariladi va to'g'ridan-to'g'ri sotib olish API endpointi orqali yangi buyurtmalar yaratiladi.

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
    customer_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    order_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Split payment fields
    is_split_payment = models.BooleanField(default=False)
    first_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    first_payment_date = models.DateTimeField(null=True, blank=True)
    second_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    second_payment_due_date = models.DateTimeField(null=True, blank=True)
    second_payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
```

## API Endpointlari

### 1. To'g'ridan-to'g'ri Sotib Olish Endpointi

Ushbu endpoint mahsulotni savatchaga qo'shmasdan to'g'ridan-to'g'ri sotib olish imkonini beradi.

**URL**: `/products/direct-purchase/`
**Method**: `POST`
**Authentication**: `X-Telegram-ID` header orqali

#### So'rov (Request)

##### Headers

```
X-Telegram-ID: <foydalanuvchi_telegram_id>
Content-Type: application/json
```

##### Body

```json
{
  "product_id": 123,
  "variant_id": 456, // ixtiyoriy
  "quantity": 1,
  "pickup_branch_id": 789,
  "payment_method": "cash_on_pickup",
  "customer_name": "John Doe",
  "phone_number": "+998901234567",
  "order_note": "Qo'shimcha ma'lumot", // ixtiyoriy
  "is_split_payment": false // ixtiyoriy
}
```

#### Javob (Response)

##### Success (201 Created)

```json
{
  "message": "Buyurtma muvaffaqiyatli yaratildi",
  "order": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "user123",
      "telegram_id": "123456789"
    },
    "total_amount": 150000.0,
    "discount_amount": 0.0,
    "shipping_amount": 0.0,
    "final_amount": 150000.0,
    "status": "pending",
    "payment_method": "cash_on_pickup",
    "payment_status": "pending",
    "customer_name": "John Doe",
    "phone_number": "+998901234567",
    "order_note": "Qo'shimcha ma'lumot",
    "created_at": "2023-08-01T14:30:00Z",
    "updated_at": "2023-08-01T14:30:00Z",
    "items": [
      {
        "id": 1,
        "product": {
          "id": 123,
          "name": "Mahsulot nomi",
          "price": 150000.0
        },
        "quantity": 1,
        "price": 150000.0,
        "total_price": 150000.0
      }
    ],
    "pickup_branch": {
      "id": 789,
      "name": "Chilonzor Do'koni",
      "address": "Chilonzor 9-kvartal"
    },
    "is_split_payment": false
  }
}
```

##### Error (400 Bad Request)

```json
{
  "message": "Mahsulot topilmadi"
}
```

##### Error (401 Unauthorized)

```json
{
  "error": "Authentication failed",
  "message": "X-Telegram-ID header is required",
  "status": 401
}
```

#### View Implementation

`DirectPurchaseView` - to'g'ridan-to'g'ri sotib olish uchun API endpoint:

```python
class DirectPurchaseView(TelegramAuthMixin, APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=DirectPurchaseSerializer,
        responses={201: OrderResponseSerializer},
        description="Mahsulotni bevosita detail sahifasidan sotib olish"
    )
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

                    # Add order item
                    variant = None
                    if data.get('variant_id'):
                        variant = ProductVariant.objects.get(id=data['variant_id'])

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        variant=variant,
                        quantity=data['quantity'],
                        price=product.discount_price or product.price
                    )

                    # Calculate totals
                    order.calculate_totals()

                    # Update product stock
                    if variant:
                        variant.stock -= data['quantity']
                        variant.save()

                    return Response({
                        'message': 'Buyurtma muvaffaqiyatli yaratildi',
                        'order': OrderSerializer(order, context={'request': request}).data
                    }, status=201)

            except Exception as e:
                return Response({
                    'message': str(e)
                }, status=400)

        return Response(serializer.errors, status=400)
```

### 2. Filiallar Endpointi

Ushbu endpoint barcha aktiv filiallar ro'yxatini olish uchun ishlatiladi.

**URL**: `/branches/`
**Method**: `GET`
**Authentication**: `X-Telegram-ID` header orqali (ixtiyoriy)

#### So'rov (Request)

##### Headers

```
X-Telegram-ID: <foydalanuvchi_telegram_id>  // ixtiyoriy
```

#### Javob (Response)

##### Success (200 OK)

```json
[
  {
    "id": 1,
    "name": "Chilonzor Do'koni",
    "branch_type": "store",
    "street": "Chilonzor 9-kvartal",
    "district": "Chilonzor",
    "city": "Toshkent",
    "region": "Toshkent shahri",
    "country": "Uzbekistan",
    "postal_code": "100000",
    "phone": "+998712345678",
    "working_hours": "09:00-20:00",
    "is_active": true,
    "location_link": "https://maps.google.com/...",
    "manager_name": "Abdullayev Abdurahmon",
    "manager_phone": "+998901234567",
    "has_fitting_room": true,
    "has_parking": true,
    "is_24_hours": false,
    "created_at": "2023-01-01T10:00:00Z",
    "updated_at": "2023-07-15T15:30:00Z"
  },
  {
    "id": 2,
    "name": "Yunusobod Pickup Punkti",
    "branch_type": "pickup",
    "street": "Amir Temur shoh ko'chasi, 108",
    "district": "Yunusobod",
    "city": "Toshkent",
    "region": "Toshkent shahri",
    "country": "Uzbekistan",
    "postal_code": "100084",
    "phone": "+998712345678",
    "working_hours": "10:00-22:00",
    "is_active": true,
    "location_link": "https://maps.google.com/...",
    "manager_name": "Karimov Shavkat",
    "manager_phone": "+998901234567",
    "has_fitting_room": false,
    "has_parking": true,
    "is_24_hours": false,
    "created_at": "2023-03-15T12:00:00Z",
    "updated_at": "2023-07-10T11:20:00Z"
  }
]
```

#### View Implementation

`ActiveBranchesView` - aktiv filiallar ro'yxatini olish uchun API endpoint:

```python
@extend_schema(
    summary="Get active branches",
    description="Get a list of all active branches (stores and pickup points)",
    tags=["Branch Management"],
    responses={
        200: serializers.ListSerializer(child=AddressSerializer()),
        401: OpenApiResponse(
            description="Authentication failed",
            response=inline_serializer(
                name='AuthError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField(),
                    'status': serializers.IntegerField(),
                }
            )
        )
    }
)
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

## Serializers

### DirectPurchaseSerializer

To'g'ridan-to'g'ri sotib olish uchun ma'lumotlarni validatsiya qilish:

```python
class DirectPurchaseSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(default=1)
    pickup_branch_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)
    customer_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    order_note = serializers.CharField(required=False, allow_blank=True)
    is_split_payment = serializers.BooleanField(default=False)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
            if not product.is_active:
                raise serializers.ValidationError("Mahsulot mavjud emas")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Mahsulot topilmadi")

    def validate_variant_id(self, value):
        if value:
            try:
                variant = ProductVariant.objects.get(id=value)
                if variant.stock <= 0:
                    raise serializers.ValidationError("Bu variant omborda yo'q")
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Variant topilmadi")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Miqdor 0 dan katta bo'lishi kerak")
        return value

    def validate_pickup_branch_id(self, value):
        try:
            branch = Address.objects.get(id=value, branch_type__in=['store', 'pickup'], is_active=True)
            return value
        except Address.DoesNotExist:
            raise serializers.ValidationError("Filial topilmadi yoki faol emas")

    def validate(self, data):
        # Check product stock
        product = Product.objects.get(id=data['product_id'])
        if data.get('variant_id'):
            variant = ProductVariant.objects.get(id=data['variant_id'])
            if variant.stock < data['quantity']:
                raise serializers.ValidationError(f"Omborda faqat {variant.stock} dona mavjud")
        else:
            # Check if any variant has enough stock
            has_stock = False
            for variant in product.variants.all():
                if variant.stock >= data['quantity']:
                    has_stock = True
                    break
            if not has_stock:
                raise serializers.ValidationError("Mahsulot omborda yo'q")

        # Validate split payment
        if data.get('is_split_payment') and data['payment_method'] != 'split':
            raise serializers.ValidationError("Bo'lib to'lash uchun payment_method 'split' bo'lishi kerak")

        return data
```

### AddressSerializer

Filiallar ma'lumotlarini serialization qilish:

```python
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'name', 'branch_type', 'street', 'district', 'city', 'region',
            'country', 'postal_code', 'phone', 'working_hours', 'is_active',
            'location_link', 'manager_name', 'manager_phone', 'has_fitting_room',
            'has_parking', 'is_24_hours', 'created_at', 'updated_at'
        ]
```

## Authenticate Mixin

`TelegramAuthMixin` - Telegram ID orqali autentifikatsiya qilish uchun mixin:

```python
class TelegramAuthMixin:
    """
    Base mixin for Telegram authentication.
    Provides common functionality for all views that require telegram authentication.
    """
    def get_user_from_telegram_id(self):
        telegram_id = self.request.META.get('HTTP_X_TELEGRAM_ID')
        if not telegram_id:
            raise exceptions.AuthenticationFailed({
                'error': 'Authentication failed',
                'message': 'X-Telegram-ID header is required',
                'status': 401
            })

        try:
            return User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed({
                'error': 'Authentication failed',
                'message': 'User not found with provided Telegram ID',
                'status': 401
            })
```

## URL Konfigurasiyalari

To'g'ridan-to'g'ri sotib olish va filiallar uchun URL konfiguratsiyalari:

```python
# Product URLs
path('products/', ProductListCreateView.as_view(), name='product-list'),
path('products/direct-purchase/', DirectPurchaseView.as_view(), name='direct-purchase'),
path('products/<slug:slug>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
path('products/<int:pk>/similar/', SimilarProductsView.as_view(), name='similar-products'),

# Branch URLs
path('branches/', ActiveBranchesView.as_view(), name='active-branches'),
```

## Xavfsizlik va Yondashuvlar

### Xavfsizlik

1. **Telegram Autentifikatsiya**: Barcha so'rovlar `X-Telegram-ID` header orqali autentifikatsiya qilinadi. Bu header mavjud bo'lmasa yoki noto'g'ri bo'lsa, so'rov rad etiladi.

2. **Permissions**:

   - `AllowAny` - Barcha foydalanuvchilar uchun, lekin autentifikatsiya `TelegramAuthMixin` orqali amalga oshiriladi
   - `IsAuthenticated` - Faqat autentifikatsiyadan o'tgan foydalanuvchilar uchun

3. **Validatsiya**: Barcha so'rovlar `serializers` orqali validatsiya qilinadi:
   - Mahsulot mavjudligi
   - Variant mavjudligi
   - Ombordagi mahsulot miqdori
   - Filial mavjudligi va faolligi
   - Bo'lib to'lash parametrlari

### Nima Uchun Bu Yondashuv Tanlandi

1. **`TelegramAuthMixin` va `AllowAny` kombinatsiyasi**:

   - `IsAuthenticated` o'rniga `AllowAny` ishlatildi, chunki autentifikatsiyani `TelegramAuthMixin` orqali qilish imkonini beradi
   - Standart DRF autentifikatsiyasidan foydalanish o'rniga, `X-Telegram-ID` headerdan foydalanildi, chunki mobil ilovada Token asosidagi autentifikatsiya qiyin

2. **URL pattern joylashuvi**:

   - `direct-purchase/` URL patterni `products/<slug:slug>/` patternidan oldin joylashtirildi, chunki Django URL patternlarni yuqoridan pastga qarab tekshiradi
   - Agar aksincha joylashtirilganda, `direct-purchase` slug sifatida qabul qilinishi va xatolikka olib kelishi mumkin edi

3. **Alohida Branches API**:

   - Filiallarni olish uchun alohida API yaratildi, chunki filiallar ro'yxati ko'p o'zgarmaydigan ma'lumot
   - Bu frontend ilovaga filiallarni oldindan olish va keshlab saqlash imkonini beradi

4. **Transaction Atomic**:
   - `transaction.atomic()` ishlatildi, chunki bir nechta modellar bilan ishlashda xatolik yuzaga kelsa, barcha o'zgarishlarni bekor qilish kerak

## Qo'llanish Misollari

### To'g'ridan-to'g'ri Sotib Olish

```javascript
// Frontend misoli (JavaScript/Fetch API)
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
      showSuccessMessage(data.message);
      redirectToOrderDetails(data.order.id);
    } else {
      // Xatolik
      showErrorMessage(data.message);
    }
  } catch (error) {
    console.error("Error during purchase:", error);
    showErrorMessage("So'rov yuborishda xatolik yuz berdi");
  }
}
```

### Filiallar Ro'yxatini Olish

```javascript
// Frontend misoli (JavaScript/Fetch API)
async function loadBranches() {
  try {
    const response = await fetch("/branches/", {
      method: "GET",
      headers: {
        "X-Telegram-ID": "123456789", // Foydalanuvchining Telegram ID (ixtiyoriy)
      },
    });

    if (response.ok) {
      const branches = await response.json();

      // Filiallarni ko'rsatish
      displayBranches(branches);

      // Keshlab saqlash
      localStorage.setItem("branches", JSON.stringify(branches));
      localStorage.setItem("branches_cached_time", Date.now());
    } else {
      showErrorMessage("Filiallar ro'yxatini olishda xatolik");
    }
  } catch (error) {
    console.error("Error loading branches:", error);

    // Keshdan o'qish, agar mavjud bo'lsa
    const cachedBranches = localStorage.getItem("branches");
    if (cachedBranches) {
      displayBranches(JSON.parse(cachedBranches));
      showWarning("Offline rejimda ishlamoqda");
    } else {
      showErrorMessage(
        "Filiallar ro'yxatini olishda xatolik va kesh mavjud emas"
      );
    }
  }
}
```

## Xulosa

To'g'ridan-to'g'ri sotib olish va filiallar API endpointlari UnicFlo API ning muhim qismi bo'lib, foydalanuvchilarga savatchadan foydalanmasdan to'g'ridan-to'g'ri mahsulotlarni sotib olish imkonini beradi.

Bu endpointlar quyidagi afzalliklarga ega:

1. **Telegram orqali autentifikatsiya** - foydalanuvchilar Telegram ID orqali autentifikatsiyadan o'tadi
2. **Validatsiya** - barcha ma'lumotlar to'liq validatsiya qilinadi (mahsulot, variant, filial, miqdor)
3. **Atomic tranzaksiyalar** - barcha o'zgarishlar bir xil tranzaksiyada bajariladi
4. **Filiallar ro'yxati** - alohida API endpointi orqali filiallar ro'yxatini olish imkoniyati
5. **Bo'lib to'lash** - mahsulotlarni bo'lib to'lash imkoniyati

Ushbu API endpointlari frontend ilovalar uchun qulay interfeys taqdim etadi va mobil ilovalar uchun optimallashtirilgan.
