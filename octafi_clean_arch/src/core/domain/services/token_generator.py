"""Serviços de domínio - lógica de negócio sem estado"""

import secrets
from datetime import datetime, timedelta

from ..value_objects import SMSToken


class TokenGenerator:
    """Gerador de tokens SMS - lógica de domínio pura"""
    
    @staticmethod
    def generate() -> SMSToken:
        """Gera token aleatório de 6 dígitos"""
        token_value = ''.join(str(secrets.randbelow(10)) for _ in range(6))
        return SMSToken(value=token_value)
    
    @staticmethod
    def calculate_expiration(minutes: int = 10) -> datetime:
        """Calcula data de expiração do token"""
        return datetime.now() + timedelta(minutes=minutes)
