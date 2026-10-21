from email_validator import validate_email
from pydantic import BaseModel, Field, SecretStr, field_validator


class EmailInput(BaseModel):
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value: str) -> str:
        # Preserve the reserved domain of existing local demo identities. No DNS lookup on login.
        local = value.lower().endswith("@local-spark.local")
        candidate = value[: -len("local")] + "test" if local else value
        normalized = validate_email(candidate, check_deliverability=False, test_environment=True).normalized
        return (normalized[: -len("test")] + "local" if local else normalized).lower()


class LoginInput(EmailInput):
    password: SecretStr = Field(min_length=1, max_length=128)


class RegisterInput(EmailInput):
    display_name: str = Field(min_length=1, max_length=120)
    password: SecretStr = Field(min_length=12, max_length=128)


class ActionInput(BaseModel):
    token: SecretStr = Field(min_length=32, max_length=128)


class ResetInput(ActionInput):
    password: SecretStr = Field(min_length=12, max_length=128)


class MFAInput(ActionInput):
    code: SecretStr = Field(min_length=6, max_length=64)
