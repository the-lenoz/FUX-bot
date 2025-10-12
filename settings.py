from datetime import timedelta

DEFAULT_TIMEZONE = timedelta(hours=3) # Moscow (GMT +3)


SUBSCRIPTION_PLANS = {
    7: 199,
    30: 399,
    90: 790
}

NEW_SUBSCRIPTION_REMINDER_PERIOD = 14

LIMITS = {
    "psychological_requests": 10,
    "universal_requests": 5,
    "exercises": 1,
    "attachments": 2,
    "voices": 2
}

LIMITS_NOTIFICATION_THRESHOLDS = {
    "psychological_requests": [5],
    "universal_requests": [3],
    "exercises": [],
    "attachments": [1],
    "voices": [1]
}

POWER_MODE_DAY_DISCOUNT = 0.015

MAX_POWER_MODE_DISCOUNT = 0.5

MAX_DAYS_FREEZE = 3


tables_to_export = [
    "admins",
    "ai_requests",
    "checkups",
    "days_checkups",
    "events",
    "exercises_user",
    "fast_help",
    "fast_help_dialogs",
    "go_deeper",
    "go_deeper_dialogs",
    "mental_problems",
    "operations",
    "promo_activations",
    "recommendations_user",
    "referral_system",
    "subscriptions",
    "summary_user",
    "users"
]

