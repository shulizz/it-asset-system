"""Canonical asset identities shared by approval and transition modules."""

from models import FireAsset, ITAsset, MedicalAsset, PhoneAsset, PhoneNumber, WeChatAccount

ASSET_MODELS = {"fire": FireAsset, "it": ITAsset, "phone": PhoneAsset, "medical": MedicalAsset}
WORKFLOW_MODELS = {**ASSET_MODELS, "number": PhoneNumber}
TABLE_ASSET_TYPES = {
    "fire_assets": "fire",
    "it_assets": "it",
    "phone_assets": "phone",
    "medical_assets": "medical",
    "phone_numbers": "number",
    "wechat_accounts": "wechat",
}
ASSET_TABLES = {
    model.__tablename__: model for model in (*ASSET_MODELS.values(), PhoneNumber, WeChatAccount)
}
