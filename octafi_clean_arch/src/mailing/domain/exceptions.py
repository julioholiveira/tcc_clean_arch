"""Exceções de domínio do Mailing"""


class MailingDomainException(Exception):
    """Base para exceções de mailing"""
    pass


class TemplateNotFoundError(MailingDomainException):
    """Template não encontrado"""
    pass


class TemplateRenderError(MailingDomainException):
    """Erro ao renderizar template"""
    pass


class CampaignStateError(MailingDomainException):
    """Estado inválido da campanha para operação"""
    pass


class RecipientValidationError(MailingDomainException):
    """Erro de validação de destinatário"""
    pass


class BulkSendError(MailingDomainException):
    """Erro no envio em lote"""
    pass
