import datetime

from django.test.testcases import TestCase

from core.models import SMSEnviado
from empresas.models import Empresa
from providers.sinch import Sinch


# @tag("no_test")
class SinchUpdateSMSStatusTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(razao_social="Teste")

        self.sms_enviados = [
            SMSEnviado(
                telefone="15997915209",
                correlation_id="781E2721-E515-11EE-AC18-00505684AD93",
                token_sms="999999",
                empresas=self.empresa,
                sms_propose="Teste",
            ),
            SMSEnviado(
                telefone="197915209",
                correlation_id="A3673591-E518-11EE-BFD8-00505684552F",
                token_sms="123456",
                empresas=self.empresa,
                sms_propose="Teste",
            ),
        ]

        SMSEnviado.objects.bulk_create(self.sms_enviados)

        self.json_response = {
            "total": 2,
            "start": "2024-03-17T11:15:08Z",
            "end": "2024-03-18T11:15:08Z",
            "smsStatuses": [
                {
                    "id": "781E2721-E515-11EE-AC18-00505684AD93",
                    "correlationId": "781E2721-E515-11EE-AC18-00505684AD93",
                    "carrierId": 1,
                    "carrierName": "VIVO",
                    "destination": "5515997915209",
                    "sentStatusCode": 2,
                    "sentStatus": "SENT_SUCCESS",
                    "sentDate": "2024-03-18T10:51:27Z",
                    "sentAt": 1710759087089,
                    "deliveredStatusCode": 4,
                    "deliveredStatus": "DELIVERED_SUCCESS",
                    "deliveredDate": "2024-03-18T10:51:29Z",
                    "deliveredAt": 1710759089357,
                    "updatedDate": "2024-03-18T10:51:54Z",
                    "updatedAt": 1710759114853,
                },
                {
                    "id": "A3673591-E518-11EE-BFD8-00505684552F",
                    "correlationId": "A3673591-E518-11EE-BFD8-00505684552F",
                    "carrierId": 0,
                    "carrierName": "TIM",
                    "destination": "55197915209",
                    "sentStatusCode": 202,
                    "sentStatus": "INVALID_DESTINATION_NUMBER",
                    "sentDate": "2024-03-18T11:14:08Z",
                    "sentAt": 1710760448009,
                    "updatedDate": "2024-03-18T11:14:16Z",
                    "updatedAt": 1710760456019,
                },
            ],
        }

    def test_sinch_update_sms_status(self):
        expected_result = [
            {
                "correlation_id": "781E2721-E515-11EE-AC18-00505684AD93",
                "sent_status": True,
                "operadora": "VIVO",
            },
            {
                "correlation_id": "A3673591-E518-11EE-BFD8-00505684552F",
                "sent_status": False,
                "operadora": "TIM",
            },
        ]
        result = Sinch.do_status_update(self.json_response)
        self.assertEqual(result, expected_result)
