"""Value Objects - Objetos imutáveis com validação intrínseca"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyId:
    """Identificador de empresa - substitui acoplamento com request/FK"""

    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Company ID must be positive")


@dataclass(frozen=True)
class PhoneNumber:
    """Número de telefone brasileiro com validação"""

    value: str

    def __post_init__(self):
        # Remove caracteres não numéricos
        cleaned = re.sub(r"\D", "", self.value)
        object.__setattr__(self, "value", cleaned)

        if not cleaned.isdigit():
            raise ValueError("Phone number must contain only digits")

        if len(cleaned) != 11:
            raise ValueError("Phone number must have 11 digits (DDD + 9 digits)")

    @property
    def formatted(self) -> str:
        """Retorna formato (XX) 9XXXX-XXXX"""
        return f"({self.value[:2]}) {self.value[2:7]}-{self.value[7:]}"

    @property
    def ddd(self) -> str:
        return self.value[:2]

    def masked(self) -> str:
        """Para logs — oculta parte do número (resolve PII sanitization)."""
        return f"{'*' * 7}{self.value[-4:]}"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CPF:
    """CPF com validação"""

    value: str

    def __post_init__(self):
        cleaned = re.sub(r"\D", "", self.value)
        object.__setattr__(self, "value", cleaned)

        if len(cleaned) != 11:
            raise ValueError("CPF must have 11 digits")

        if not self._is_valid():
            raise ValueError("Invalid CPF")

    def _is_valid(self) -> bool:
        """Validação de dígitos verificadores"""
        if self.value in [d * 11 for d in "0123456789"]:
            return False

        # Primeiro dígito
        sum_digits = sum(int(self.value[i]) * (10 - i) for i in range(9))
        digit1 = (sum_digits * 10 % 11) % 10

        # Segundo dígito
        sum_digits = sum(int(self.value[i]) * (11 - i) for i in range(10))
        digit2 = (sum_digits * 10 % 11) % 10

        return self.value[-2:] == f"{digit1}{digit2}"

    @property
    def formatted(self) -> str:
        """Retorna formato XXX.XXX.XXX-XX"""
        return f"{self.value[:3]}.{self.value[3:6]}.{self.value[6:9]}-{self.value[9:]}"

    @property
    def masked(self) -> str:
        """Para logs - oculta parte do CPF"""
        return f"***.***.{self.value[6:9]}-**"


@dataclass(frozen=True)
class MACAddress:
    """Endereço MAC de dispositivo de rede"""

    value: str

    def __post_init__(self):
        cleaned = re.sub(r"[:-]", "", self.value).upper()
        object.__setattr__(self, "value", cleaned)

        if not re.match(r"^[0-9A-F]{12}$", cleaned):
            raise ValueError("Invalid MAC address format")

    @property
    def formatted(self) -> str:
        """Retorna formato XX:XX:XX:XX:XX:XX"""
        mac = self.value
        return ":".join(mac[i : i + 2] for i in range(0, 12, 2))


@dataclass(frozen=True)
class SMSToken:
    """Token de verificação SMS (6 dígitos)"""

    value: str

    def __post_init__(self):
        if not self.value.isdigit():
            raise ValueError("Token must contain only digits")

        if len(self.value) != 6:
            raise ValueError("Token must have exactly 6 digits")

        object.__setattr__(self, "value", self.value)

    def __str__(self) -> str:
        return self.value
