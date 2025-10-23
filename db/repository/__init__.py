from .admin_repo import AdminRepository
from .ai_requests_repo import AiRequestsRepository
from .checkups_repo import CheckupRepository
from .days_checkups_repo import DaysCheckupRepository
from .discount_repo import DiscountRepository
from .events_repo import EventsRepository
from .exercises_user_repo import ExercisesUserRepository
from .limits_repo import LimitsRepository
from .mental_problems_repo import MentalProblemsRepository
from .operations_repo import OperationRepository
from .payment_methods_repo import PaymentMethodsRepository
from .pending_messages_repo import PendingMessagesRepository
from .promo_activations_repo import PromoActivationsRepository
from .recommendations_repo import RecommendationsRepository
from .refferal_repo import ReferralSystemRepository
from .subscriptions_repo import SubscriptionsRepository
from .user_counters_repo import UserCountersRepository
from .user_timezone_repo import UserTimezoneRepository
from .users_repo import UserRepository


users_repository = UserRepository()
admin_repository = AdminRepository()
ai_requests_repository = AiRequestsRepository()
referral_system_repository = ReferralSystemRepository()
promo_activations_repository = PromoActivationsRepository()
subscriptions_repository = SubscriptionsRepository()
operation_repository = OperationRepository()
checkup_repository = CheckupRepository()
days_checkups_repository = DaysCheckupRepository()
exercises_user_repository = ExercisesUserRepository()
events_repository = EventsRepository()
mental_problems_repository = MentalProblemsRepository()
recommendations_repository = RecommendationsRepository()
user_timezone_repository = UserTimezoneRepository()
limits_repository = LimitsRepository()
pending_messages_repository = PendingMessagesRepository()
user_counters_repository = UserCountersRepository()
payment_methods_repository = PaymentMethodsRepository()
discount_repository = DiscountRepository()

__all__ = ['users_repository',
           'admin_repository',
           'ai_requests_repository',
           'referral_system_repository',
           'promo_activations_repository',
           'subscriptions_repository',
           'operation_repository',
           'checkup_repository',
           'days_checkups_repository',
           'exercises_user_repository',
           'events_repository',
           'mental_problems_repository',
           'recommendations_repository',
           'user_timezone_repository',
           'limits_repository',
           'pending_messages_repository',
           'user_counters_repository',
           'payment_methods_repository',
           'discount_repository'
          ]