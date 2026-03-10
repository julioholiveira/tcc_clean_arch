"""Validação avançada de telefone - serviço de domínio"""

from typing import List

from ..value_objects import PhoneNumber
from ..exceptions import ValidationError


class PhoneValidator:
    """Validações específicas de negócio para telefones"""
    
    # DDDs válidos no Brasil (principais)
    VALID_DDDS = {
        '11', '12', '13', '14', '15', '16', '17', '18', '19',  # SP
        '21', '22', '24',  # RJ
        '27', '28',  # ES
        '31', '32', '33', '34', '35', '37', '38',  # MG
        '41', '42', '43', '44', '45', '46',  # PR
        '47', '48', '49',  # SC
        '51', '53', '54', '55',  # RS
        '61',  # DF
        '62', '64',  # GO
        '63',  # TO
        '65', '66',  # MT
        '67',  # MS
        '68',  # AC
        '69',  # RO
        '71', '73', '74', '75', '77',  # BA
        '79',  # SE
        '81', '87',  # PE
        '82',  # AL
        '83',  # PB
        '84',  # RN
        '85', '88',  # CE
        '86', '89',  # PI
        '91', '93', '94',  # PA
        '92', '97',  # AM
        '95',  # RR
        '96',  # AP
        '98', '99',  # MA
    }
    
    @classmethod
    def validate_ddd(cls, phone: PhoneNumber) -> None:
        """Valida se DDD é válido"""
        if phone.ddd not in cls.VALID_DDDS:
            raise ValidationError(f"Invalid DDD: {phone.ddd}")
    
    @classmethod
    def is_blacklisted(cls, phone: PhoneNumber, blacklist: List[str]) -> bool:
        """Verifica se telefone está em lista negra"""
        return phone.value in blacklist
    
    @classmethod
    def normalize_for_provider(cls, phone: PhoneNumber, country_code: str = '55') -> str:
        """Normaliza para envio via provider (com código do país)"""
        return f"+{country_code}{phone.value}"
