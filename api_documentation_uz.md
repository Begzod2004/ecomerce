# UnicFlo API Dokumentatsiyasi

## Loyiha haqida

UnicFlo - bu zamonaviy elektron tijorat platformasi uchun REST API. API Django Rest Framework yordamida yaratilgan va quyidagi asosiy funksiyalarni o'z ichiga oladi:

- Foydalanuvchilarni boshqarish
- Mahsulotlarni boshqarish
- Buyurtmalarni boshqarish
- Savatcha funksionalligi
- Bo'lib to'lash tizimi

### Loyiha maqsadi

UnicFlo - O'zbekistondagi kiyim-kechak va aksessuarlar sohasidagi elektron tijorat platformasi. Loyihaning asosiy maqsadi mijozlarga qulay va zamonaviy onlayn xarid qilish imkoniyatini taqdim etish, hamda sotuvchilar uchun o'z mahsulotlarini samarali sotish platformasini yaratish.

### Asosiy foydalanuvchilar

1. **Xaridorlar**

   - Telegram orqali ro'yxatdan o'tgan foydalanuvchilar
   - Onlayn xarid qiluvchi mijozlar
   - Bo'lib to'lash xizmatidan foydalanuvchilar

2. **Sotuvchilar**

   - Do'konlar
   - Brendlar
   - Individual sotuvchilar

3. **Administratorlar**
   - Platforma moderatorlari
   - Kontentni boshqaruvchilar
   - Buyurtmalarni nazorat qiluvchilar

### Asosiy funksionallik

1. **Telegram integratsiyasi**

   - Telegram orqali ro'yxatdan o'tish
   - Telegram bot orqali buyurtma berish
   - Bildirishnomalarni olish

2. **Mahsulotlar katalogi**

   - Kategoriyalar bo'yicha mahsulotlarni ko'rish
   - Qidiruv va filtrlash
   - Mahsulot variantlari (rang, o'lcham)

3. **Xarid qilish**

   - Savatchaga qo'shish
   - To'g'ridan-to'g'ri sotib olish
   - Bo'lib to'lash imkoniyati

4. **Yetkazib berish**
   - Do'kondan olib ketish
   - Kuryer orqali yetkazib berish
   - Filiallardan olib ketish

## User Story'lar

### Xaridor (Mijoz) uchun

1. **Ro'yxatdan o'tish**

   ```
   SIFATIDA xaridor
   MEN Telegram orqali tizimga kirmoqchiman
   CHUNKI bu orqali tez va oson ro'yxatdan o'tish mumkin
   ```

2. **Mahsulotlarni ko'rish**

   ```
   SIFATIDA xaridor
   MEN barcha mavjud mahsulotlarni ko'rmoqchiman
   CHUNKI men o'zimga kerakli mahsulotni tanlamoqchiman
   ```

3. **Mahsulotni qidirish**

   ```
   SIFATIDA xaridor
   MEN mahsulotlarni qidirish va filtrlash imkoniyatidan foydalanmoqchiman
   CHUNKI men o'zimga kerakli mahsulotni tezroq topmoqchiman
   ```

4. **Savatchaga qo'shish**

   ```
   SIFATIDA xaridor
   MEN mahsulotlarni savatchaga qo'shmoqchiman
   CHUNKI men bir nechta mahsulotni birga xarid qilmoqchiman
   ```

5. **Bo'lib to'lash**
   ```
   SIFATIDA xaridor
   MEN mahsulotni bo'lib to'lash orqali sotib olmoqchiman
   CHUNKI men to'lovni ikki qismga bo'lib to'lamoqchiman
   ```

### Sotuvchi uchun

1. **Mahsulot qo'shish**

   ```
   SIFATIDA sotuvchi
   MEN yangi mahsulot qo'shmoqchiman
   CHUNKI men yangi mahsulotlarimni sotuvga qo'ymoqchiman
   ```

2. **Buyurtmalarni ko'rish**

   ```
   SIFATIDA sotuvchi
   MEN barcha buyurtmalarni ko'rmoqchiman
   CHUNKI men buyurtmalarni boshqarmoqchiman
   ```

3. **Statistikani ko'rish**
   ```
   SIFATIDA sotuvchi
   MEN sotuvlar statistikasini ko'rmoqchiman
   CHUNKI men biznesimni tahlil qilmoqchiman
   ```

### Administrator uchun

1. **Foydalanuvchilarni boshqarish**

   ```
   SIFATIDA administrator
   MEN foydalanuvchilarni boshqarmoqchiman
   CHUNKI men platformada tartibni saqlamoqchiman
   ```

2. **Kontentni moderatsiya qilish**

   ```
   SIFATIDA administrator
   MEN mahsulotlar kontentini tekshirmoqchiman
   CHUNKI sifatli kontent muhim
   ```

3. **Buyurtmalarni nazorat qilish**
   ```
   SIFATIDA administrator
   MEN buyurtmalar holatini nazorat qilmoqchiman
   CHUNKI men yetkazib berish jarayonini optimallashtirishim kerak
   ```

### Texnik xususiyatlar

1. **Xavfsizlik**

   ```
   SIFATIDA tizim administratori
   MEN barcha operatsiyalar xavfsiz bo'lishini ta'minlamoqchiman
   CHUNKI foydalanuvchilar ma'lumotlari muhofaza qilinishi kerak
   ```

2. **Ishlash tezligi**

   ```
   SIFATIDA tizim administratori
   MEN API tez ishlashini ta'minlamoqchiman
   CHUNKI foydalanuvchilar tajribasi muhim
   ```

3. **Monitoring**
   ```
   SIFATIDA tizim administratori
   MEN tizim ishlashini kuzatmoqchiman
   CHUNKI xatolarni tezda aniqlash va tuzatish kerak
   ```

## Autentifikatsiya

API Telegram orqali autentifikatsiyadan foydalanadi.

**Header formati:**

```http
X-Telegram-ID: <telegram_user_id>
```

## API Endpointlari

### 1. Foydalanuvchilar

#### Foydalanuvchilar ro'yxati

```http
GET /api/users/
```

**Javob (200 OK):**

```json
{
  "count": 100,
  "next": "/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "telegram_id": "123456789",
      "telegram_username": "username",
      "first_name": "Ism",
      "last_name": "Familiya",
      "phone_number": "+998901234567"
    }
  ]
}
```

#### Joriy foydalanuvchi ma'lumotlari

```http
GET /api/users/me/
```

### 2. Mahsulotlar

#### Mahsulotlar ro'yxati

```http
GET /api/products/
```

**Filtrlash parametrlari:**

- `category` - Kategoriya bo'yicha
- `subcategory` - Subkategoriya bo'yicha
- `brand` - Brend bo'yicha
- `price_min` - Minimal narx
- `price_max` - Maksimal narx
- `search` - Qidiruv so'zi

**Javob (200 OK):**

```json
{
  "count": 100,
  "next": "/api/products/?page=2",
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

### 3. Savatcha

#### Savatchaga qo'shish

```http
POST /api/cart/add/
```

**So'rov:**

```json
{
  "product_id": 1,
  "variant_id": 1,
  "quantity": 2
}
```

#### Savatcha ma'lumotlari

```http
GET /api/cart/
```

### 4. Buyurtmalar

#### Buyurtma yaratish

```http
POST /api/orders/
```

**So'rov:**

```json
{
  "cart_id": 1,
  "pickup_branch_id": 2,
  "customer_name": "Ism Familiya",
  "phone_number": "+998901234567",
  "payment_method": "cash_on_pickup",
  "is_split_payment": false
}
```

### 5. Bo'lib to'lash

Bo'lib to'lash uchun `is_split_payment` parametrini `true` qilib yuborish kerak:

```json
{
  "cart_id": 1,
  "pickup_branch_id": 2,
  "customer_name": "Ism Familiya",
  "phone_number": "+998901234567",
  "payment_method": "split",
  "is_split_payment": true
}
```

## Xatoliklar

API quyidagi xatolik kodlarini qaytarishi mumkin:

- `400 Bad Request` - So'rovda xatolik
- `401 Unauthorized` - Autentifikatsiya talab qilinadi
- `403 Forbidden` - Ruxsat berilmagan
- `404 Not Found` - Ma'lumot topilmadi
- `500 Internal Server Error` - Serverda xatolik

## Sahifalash

Barcha ro'yxat endpointlari sahifalashni qo'llab-quvvatlaydi:

- `page` - Sahifa raqami
- `page_size` - Har bir sahifadagi elementlar soni (default: 10)

Misol:

```http
GET /api/products/?page=2&page_size=20
```

## Qidiruv va Filtrlash

Ko'pgina endpointlar qidiruv va filtrlash imkoniyatlarini taqdim etadi:

### Qidiruv

```http
GET /api/products/?search=kurtka
```

### Filtrlash

```http
GET /api/products/?category=1&price_min=100000&price_max=500000
```

## Tartiblash

Ma'lumotlarni tartiblash uchun `ordering` parametridan foydalaning:

```http
GET /api/products/?ordering=-price
```

- `price` - Narx bo'yicha o'sish tartibida
- `-price` - Narx bo'yicha kamayish tartibida
- `created_at` - Yaratilgan vaqti bo'yicha
- `-created_at` - Yaratilgan vaqti bo'yicha (teskari tartibda)

## Middleware va Permissions

### TelegramWebAppAuthMiddleware

Telegram Web App orqali kelgan so'rovlarni autentifikatsiya qilish uchun middleware.

### IsAuthenticated

Barcha endpointlar uchun autentifikatsiya talab qilinadi (agar alohida ko'rsatilmagan bo'lsa).

## API Versiyalash

Hozirda API v1 versiyasida ishlaydi. Keyingi versiyalar uchun endpoint prefixlari qo'shiladi:

```http
/api/v2/...
```

## Rate Limiting

API so'rovlar sonini cheklash tizimi mavjud:

- Ro'yxatdan o'tmagan foydalanuvchilar: 100 so'rov/soat
- Ro'yxatdan o'tgan foydalanuvchilar: 1000 so'rov/soat
- Admin foydalanuvchilar: Cheklovsiz

## Xavfsizlik

1. Barcha so'rovlar HTTPS orqali yuborilishi shart
2. Telegram ID headerini to'g'ri formatda yuborish kerak
3. Maxfiy ma'lumotlar (API kalitlari, tokenlar) so'rovlarda ochiq yuborilmasligi kerak

## Texnik Talablar

- Python 3.8+
- Django 4.2+
- Django REST Framework 3.14+
- PostgreSQL 13+ (yoki SQLite development uchun)

## Qo'shimcha Ma'lumot

To'liq texnik hujjatlar va yangilanishlar uchun rasmiy repozitoriyga murojaat qiling:
[https://github.com/unicflo/api](https://github.com/unicflo/api)
