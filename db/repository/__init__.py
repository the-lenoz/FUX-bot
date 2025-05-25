from .admin_repo import AdminRepository
from .ai_requests_repo import AiRequestsRepository
from .checkups_repo import CheckupRepository
from .days_checkups_repo import DaysCheckupRepository
from .events_repo import EventsRepository
from .exercises_user_repo import ExercisesUserRepository
from .mental_problems_repo import MentalProblemsRepository
from .operations_repo import OperationRepository
from .promo_activations_repo import PromoActivationsRepository
from .refferal_repo import ReferralSystemRepository
from .subscriptions_repo import SubscriptionsRepository
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
mental_problems_repository = MentalProblemsRepository()
exercises_user_repository = ExercisesUserRepository()
events_repository = EventsRepository()

__all__ = ['users_repository',
           'admin_repository',
           'ai_requests_repository',
           'referral_system_repository',
           'promo_activations_repository',
           'subscriptions_repository',
           'operation_repository',
           'checkup_repository',
           'days_checkups_repository',
           'mental_problems_repository',
           'exercises_user_repository',
           'events_repository'
          ]