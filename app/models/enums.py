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


class AdminRole(StrEnum):
    """Owner can manage other admins and override anything; support is everyday
    read/write operations; viewer is read-only (e.g. an accountant or auditor)."""

    OWNER = "owner"
    SUPPORT = "support"
    VIEWER = "viewer"


class EyebrowStyle(StrEnum):
    NATURAL_FILL = "natural_fill"
    SOFT_ARCH = "soft_arch"
    BOLD_DEFINED = "bold_defined"
    STRAIGHT = "straight"


class LashStyle(StrEnum):
    NATURAL = "natural"
    WISPY = "wispy"
    DRAMATIC = "dramatic"
    DOLL_EYE = "doll_eye"


class GeleStyle(StrEnum):
    AUTO_GELE = "auto_gele"
    IPELE = "ipele"
    SIMPLE_WRAP = "simple_wrap"
    WIG_STRAIGHT = "wig_straight"
    WIG_CURLY = "wig_curly"
