from pathlib import Path
import os
from django.templatetags.static import static
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
SECRET_KEY = 'django-insecure-*4mg3zssza0j_23z$^d(1d-w+q89u$_@w%=^o_gvl)m3wbbke2'
DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    "unfold",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework.authtoken",
    "rest_framework",
    "django_celery_beat",
    "corsheaders",
    "drf_spectacular",

    #apps
    "apps.users",
    "apps.main",
    "apps.delivery",
    "apps.taxi",
    "apps.maps",
    "apps.balance",
    "apps.notify",
    "apps.payments",
    "apps.health"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST":  os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',

    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}




AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
AUTH_USER_MODEL = 'users.User'



LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Asia/Bishkek'

USE_I18N = True

USE_TZ = True


ASGI_APPLICATION = "core.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CSRF_TRUSTED_ORIGINS = [
    "https://ego.kg",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
APPEND_SLASH=False
REDIS_URL = "redis://127.0.0.1:6379/0"
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL


NAMBA_SECRET = os.getenv("NAMBA_API_KEY")
NAMBA_MERCHANT_ID = os.getenv("NAMBA_MERCHANT_ID")
NAMBA_SECRET_DRIVERS = os.getenv("NAMBA_API_KEY_DRIVERS")
NAMBA_MERCHANT_ID_DRIVERS = os.getenv("NAMBA_MERCHANT_ID_DRIVERS")
NAMBA_BASE_URL = os.getenv("NAMBA_BASE_URL")
NAMBA_WEBHOOK_URL = os.getenv("NAMBA_WEBHOOK_URL")

DOMAIN = "https://ego.kg"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Bishkek"
ONESIGNAL_APP_ID = os.getenv("ONESIGNAL_APP_ID", "")
ONESIGNAL_API_KEY = "os_v2_app_owmo3xulfbcfvgcckc5pibakasp4n5quydbupzmw6ox5clwu4iptaycqdbwnqub2l5hjvyzlu7j3lvvfjf6gr2sjszjv6pmhirkgl5y"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

NIKITA_LOGIN = os.getenv("NIKITA_LOGIN")
NIKITA_PASSWORD = os.getenv("NIKITA_PASSWORD")
NIKITA_SENDER = os.getenv("NIKITA_SENDER")
YANDEX_GEOCODER_API_KEY = os.getenv("YANDEX_GEOCODER_API_KEY")
YANDEX_SUGGEST_API_KEY = os.getenv("YANDEX_SUGGEST_API_KEY")
YANDEX_DISTANCE_MATRIX_API_KEY = os.getenv("YANDEX_DISTANCE_MATRIX_API_KEY", default="")
YANDEX_DISTANCE_MATRIX_TIMEOUT = 10
DEFAULT_TAXI_CITY = "Бишкек"
MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", default="")
MAPBOX_DISTANCE_MATRIX_TIMEOUT = 10

from django.templatetags.static import static

UNFOLD = {

    "SITE_TITLE": "EGO Admin",
    "SITE_HEADER": "EGO",
    "SITE_SYMBOL": "blur_on",

    "SITE_LOGO": {
        "light": lambda request: "/media/image5.png",
        "dark": lambda request: "/media/image5.png",
    },

    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "80x70",
            "href": "/media/image6.png",
        },
    ],

    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,

    "DARK_MODE": True,

    "STYLES": [
        lambda request: static("css/admin-fix.css"),
        lambda request: static("css/ego-admnn.css"),
    ],


    "SIDEBAR": {

        "show_all_applications": False,

        "navigation": [
            {
                "title": "Операции",
                "icon": "directions_car",
                "separator": True,
                "items": [

                    {
                        "title": "Заказы доставки",
                        "icon": "shopping_bag",
                        "link": "/admin/delivery/delivery/",
                    },

                    {
                        "title": "Офферы доставки",
                        "icon": "move_up",
                        "link": "/admin/delivery/deliveryoffer/",
                    },

                    {
                        "title": "Поездки такси",
                        "icon": "local_taxi",
                        "link": "/admin/taxi/taxiride/",
                    },
                ],
            },
            {
                "title": "Курьеры",
                "icon": "two_wheeler",
                "separator": True,
                "items": [

                    {
                        "title": "Диспетчерская курьеров",
                        "icon": "delivery_dining",
                        "link": "/admin/users/courierdispatch/",
                    },

                    {
                        "title": "Слоты курьеров",
                        "icon": "schedule",
                        "link": "/admin/delivery/courierslot/",
                    },
                    {
                        "title": "Здоровье",
                        "icon": "monitor_heart",
                        "link": "/admin/health/",
                    },

                    {
                        "title": "Маршруты",
                        "icon": "route",
                        "link": "/admin/delivery/courierroute/",
                    },

                    {
                        "title": "Точки маршрута",
                        "icon": "alt_route",
                        "link": "/admin/delivery/courierroutestop/",
                    },
                ],
            },

            {
                "title": "Таксисты",
                "icon": "airport_shuttle",
                "separator": True,
                "items": [

                    {
                        "title": "Диспетчерская таксистов",
                        "icon": "local_taxi",
                        "link": "/admin/users/driverdispatch/",
                    },
                ],
            },
            {
                "title": "Финансы",
                "icon": "account_balance_wallet",
                "separator": True,
                "items": [

                    {
                        "title": "Кошельки",
                        "icon": "wallet",
                        "link": "/admin/balance/workerwallet/",
                    },

                    {
                        "title": "Транзакции",
                        "icon": "payments",
                        "link": "/admin/balance/wallettransaction/",
                    },

                    {
                        "title": "Вывод средств",
                        "icon": "credit_card",
                        "link": "/admin/balance/withdrawalrequest/",
                    },

                    {
                        "title": "Платежи",
                        "icon": "receipt_long",
                        "link": "/admin/payments/payment/",
                    },
                    {
                        "title": "Трансферы Namba One",
                        "icon": "receipt_long",
                        "link": "/admin/payments/nambatransfer/",
                    },

                ],
            },
            {
                "title": "Бонусная система",
                "icon": "workspace_premium",
                "separator": True,
                "items": [

                    {
                        "title": "Бонусные правила",
                        "icon": "military_tech",
                        "link": "/admin/balance/bonusrule/",
                    },

                    {
                        "title": "Бонусные миссии",
                        "icon": "emoji_events",
                        "link": "/admin/balance/bonusmission/",
                    },

                    {
                        "title": "Прогресс миссий",
                        "icon": "trending_up",
                        "link": "/admin/balance/workermissionprogress/",
                    },

                    {
                        "title": "Начисления бонусов",
                        "icon": "redeem",
                        "link": "/admin/balance/bonusreward/",
                    },
                ],
            },

            {
                "title": "География",
                "icon": "place",
                "separator": True,
                "items": [

                    {
                        "title": "Дарксторы",
                        "icon": "store",
                        "link": "/admin/main/darkstore/",
                    },

                    {
                        "title": "Зоны доставки",
                        "icon": "map",
                        "link": "/admin/main/deliveryzone/",
                    },

                    {
                        "title": "Отзывы",
                        "icon": "map",
                        "link": "/admin/main/review/",
                    },

                ],
            },

            {
                "title": "Тарифы",
                "icon": "monitoring",
                "separator": True,
                "items": [

                    {
                        "title": "Тарифы такси",
                        "icon": "price_change",
                        "link": "/admin/main/tariff/",
                    },

                    {
                        "title": "Тарифы доставки",
                        "icon": "local_shipping",
                        "link": "/admin/main/deliverytariff/",
                    },

                    {
                        "title": "Комиссии доставки",
                        "icon": "local_shipping",
                        "link": "/admin/main/deliverycommission/",
                    },

                    {
                        "title": "Комиссии такси",
                        "icon": "local_taxi",
                        "link": "/admin/main/taxicommission/",
                    },


                ],
            },


            {
                "title": "Пользователи",
                "icon": "groups",
                "separator": True,
                "items": [

                    {
                        "title": "Клиенты",
                        "icon": "person",
                        "link": "/admin/users/client/",
                    },

                    {
                        "title": "Операторы",
                        "icon": "support_agent",
                        "link": "/admin/users/operator/",
                    },

                    {
                        "title": "Администраторы",
                        "icon": "admin_panel_settings",
                        "link": "/admin/users/admin/",
                    },
                ],
            },
            {
                "title": "Уведомления",
                "icon": "notifications",
                "separator": True,
                "items": [

                    {
                        "title": "Push устройства",
                        "icon": "phone_android",
                        "link": "/admin/notify/pushdevice/",
                    },

                    {
                        "title": "Push уведомления",
                        "icon": "notifications_active",
                        "link": "/admin/notify/pushnotification/",
                    },
                ],
            },
            {
                "title": "Система",
                "icon": "settings",
                "separator": True,
                "items": [

                    {
                        "title": "API Tokens",
                        "icon": "vpn_key",
                        "link": "/admin/authtoken/tokenproxy/",
                    },
                ],
            },
        ],
    },
}