from enum import StrEnum


class AccountType(StrEnum):
    CONSUMER = "consumer"
    BUSINESS = "business"


class ClientTag(StrEnum):
    SELF = "self"
    CLIENT = "client"


class ShadeCategory(StrEnum):
    LIPSTICK = "lipstick"
    FOUNDATION = "foundation"
    POWDER = "powder"
    EYESHADOW = "eyeshadow"
    BLUSH = "blush"


class ShadeFinish(StrEnum):
    MATTE = "matte"
    GLOSSY = "glossy"
    SHIMMER = "shimmer"
    SATIN = "satin"


class SubscriptionPlan(StrEnum):
    SOLO = "solo"
    STUDIO = "studio"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class EnhanceJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
