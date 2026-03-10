"""Implementação Django ORM do UserRepository e ConnectionRepository."""

from datetime import datetime, timedelta
from typing import List, Optional

from django.utils.timezone import make_aware

from core.models import Historico, Usuario
from src.core.domain.entities import Connection, User
from src.core.domain.repositories import ConnectionRepository, UserRepository
from src.core.domain.value_objects import CompanyId, MACAddress, PhoneNumber


class DjangoUserRepository(UserRepository):
    """
    Adaptador ORM Django para a entidade User.
    Resolve P3: filtragem por empresa sai do model e vai para o repository
    com parâmetro company_id (não request) — resolve ISP P11.
    """

    @staticmethod
    def _to_domain(orm: Usuario) -> User:
        return User(
            id=orm.pk,
            company_id=CompanyId(orm.empresas_id),
            phone=PhoneNumber(orm.telefone),
            name=orm.nome_usuario,
            cpf=orm.cpf_usuario,
            created_at=orm.criacao,
        )

    @staticmethod
    def _to_orm_kwargs(user: User) -> dict:
        return {
            "telefone": user.phone.value,
            "empresas_id": user.company_id.value,
            "nome_usuario": user.name,
            "cpf_usuario": user.cpf,
        }

    def save(self, user: User) -> User:
        if user.id:
            Usuario.objects.filter(pk=user.id).update(**self._to_orm_kwargs(user))
            orm = Usuario.objects.get(pk=user.id)
        else:
            orm = Usuario.objects.create(**self._to_orm_kwargs(user))
        return self._to_domain(orm)

    def find_by_id(self, user_id: int) -> Optional[User]:
        try:
            return self._to_domain(Usuario.objects.get(pk=user_id))
        except Usuario.DoesNotExist:
            return None

    def find_by_phone(self, company_id: CompanyId, phone: PhoneNumber) -> Optional[User]:
        try:
            return self._to_domain(
                Usuario.objects.get(
                    telefone=phone.value,
                    empresas_id=company_id.value,
                )
            )
        except Usuario.DoesNotExist:
            return None

    def list_by_company(
        self,
        company_id: CompanyId,
        limit: int = 100,
        offset: int = 0,
    ) -> List[User]:
        """
        Resolve P3: lógica de get_guest_users sai do model para o repository.
        Recebe company_id em vez do objeto request (resolve ISP P11).
        """
        qs = Usuario.objects.filter(empresas_id=company_id.value).order_by("-criacao")[offset : offset + limit]
        return [self._to_domain(u) for u in qs]


class DjangoConnectionRepository(ConnectionRepository):
    """
    Adaptador ORM Django para Historico (conexões de rede).
    Resolve P3: lógica de count/filtragem sai do model para o repository.
    """

    @staticmethod
    def _to_domain(orm: Historico) -> Connection:
        return Connection(
            id=orm.pk,
            company_id=CompanyId(orm.empresas_id),
            user_phone=PhoneNumber(orm.usuarios.telefone if orm.usuarios else "00000000000"),
            mac_address=MACAddress(orm.mac),
            controller_name="unifi",
            ip_address=str(orm.ip) if orm.ip else None,
            connected_at=orm.data_conexao,
        )

    def save(self, connection: Connection) -> Connection:
        orm = Historico.objects.create(
            empresas_id=connection.company_id.value,
            mac=connection.mac_address.value,
            ip=connection.ip_address or "127.0.0.1",
            data_conexao=connection.connected_at or make_aware(datetime.now()),
        )
        return self._to_domain(orm)

    def count_active_connections(self, company_id: CompanyId, user_phone: PhoneNumber) -> int:
        """Conta conexões ativas do usuário — resolve ISP P11 (recebe company_id, não request)."""
        return Historico.objects.filter(
            empresas_id=company_id.value,
            usuarios__telefone=user_phone.value,
        ).count()

    def count_today_by_mac(self, company_id: CompanyId, mac_address: MACAddress) -> int:
        """
        Conta conexões do mesmo MAC hoje.
        Resolve P3 (SRP) e P11 (ISP): parâmetros específicos em vez de request.
        """
        from datetime import date

        return Historico.objects.filter(
            empresas_id=company_id.value,
            mac__exact=mac_address.value,
            data_conexao__date=date.today(),
        ).count()

    def count_last_24h(self, company_id: CompanyId) -> int:
        threshold = make_aware(datetime.now() - timedelta(days=1))
        return Historico.objects.filter(
            empresas_id=company_id.value,
            data_conexao__gte=threshold,
        ).count()

    def list_by_user(
        self,
        company_id: CompanyId,
        user_phone: PhoneNumber,
        limit: int = 50,
    ) -> List[Connection]:
        qs = (
            Historico.objects.filter(
                empresas_id=company_id.value,
                usuarios__telefone=user_phone.value,
            )
            .select_related("usuarios")
            .order_by("-data_conexao")[:limit]
        )
        return [self._to_domain(h) for h in qs]
