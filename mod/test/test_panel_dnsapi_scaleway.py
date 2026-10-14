import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class HintException(Exception):
    pass


def load_panel_dnsapi():
    fake_public = types.ModuleType("public")
    fake_public.__path__ = []
    fake_public.split_domain_sld = lambda domain: (domain, "")
    fake_public.get_panel_path = lambda: "/www/server/panel"

    fake_exceptions = types.ModuleType("public.exceptions")
    fake_exceptions.HintException = HintException
    fake_public.exceptions = fake_exceptions

    fake_requests = types.ModuleType("requests")
    fake_requests.Response = object
    fake_requests.RequestException = OSError
    fake_requests.exceptions = types.SimpleNamespace(
        HTTPError=OSError,
        RequestException=OSError,
    )
    fake_requests.request = mock.Mock()

    module_path = Path(__file__).resolve().parents[2] / "class" / "panelDnsapi.py"
    spec = importlib.util.spec_from_file_location("panelDnsapi_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(
            sys.modules,
            {
                "public": fake_public,
                "public.exceptions": fake_exceptions,
                "requests": fake_requests,
            },
    ), mock.patch.object(os, "chdir"):
        spec.loader.exec_module(module)
    return module


panel_dnsapi = load_panel_dnsapi()
ScalewayDns = panel_dnsapi.ScalewayDns


class FakeResponse:
    def __init__(self, data=None, status_code=200, text=None):
        self._data = {} if data is None else data
        self.status_code = status_code
        self.text = text if text is not None else str(self._data)
        self.content = self.text.encode()

    def json(self):
        return self._data


def zones_response():
    return FakeResponse({
        "total_count": 2,
        "dns_zones": [
            {"domain": "example.com", "subdomain": "", "status": "active"},
            {"domain": "example.com", "subdomain": "dev", "status": "active"},
        ],
    })


class ScalewayDnsTest(unittest.TestCase):
    def test_dns01_add_uses_longest_zone_and_safe_payload(self):
        responses = [
            zones_response(),
            FakeResponse({"total_count": 0, "records": []}),
            FakeResponse({"records": [{"id": "new-record"}]}),
        ]
        with mock.patch.object(panel_dnsapi.requests, "request", side_effect=responses) as request:
            # The third positional argument exercises acme_v2's legacy fallback.
            provider = ScalewayDns("unused-access-key", "secret-key", True)
            self.assertTrue(provider.create_dns_record("*.api.dev.example.com", "challenge-token"))

        record_get = request.call_args_list[1]
        self.assertTrue(record_get.args[1].endswith("/dns-zones/dev.example.com/records"))
        self.assertEqual(record_get.kwargs["params"]["name"], "_acme-challenge.api")
        self.assertEqual(record_get.kwargs["params"]["type"], "TXT")

        patch_call = request.call_args_list[2]
        self.assertEqual(patch_call.args[0], "PATCH")
        self.assertEqual(patch_call.kwargs["headers"]["X-Auth-Token"], "secret-key")
        self.assertNotIn("unused-access-key", patch_call.kwargs["headers"].values())
        self.assertEqual(patch_call.kwargs["json"], {
            "return_all_records": False,
            "disallow_new_zone_creation": True,
            "changes": [{"add": {"records": [{
                "name": "_acme-challenge.api",
                "data": "challenge-token",
                "type": "TXT",
                "ttl": 60,
            }]}}],
        })

    def test_dns01_delete_targets_only_matching_txt_value(self):
        responses = [
            zones_response(),
            FakeResponse({
                "total_count": 2,
                "records": [
                    {"id": "wanted", "name": "_acme-challenge.api", "type": "TXT",
                     "data": '"challenge-token"', "ttl": 60},
                    {"id": "keep", "name": "_acme-challenge.api", "type": "TXT",
                     "data": '"another-token"', "ttl": 60},
                ],
            }),
            FakeResponse({"records": []}),
        ]
        with mock.patch.object(panel_dnsapi.requests, "request", side_effect=responses) as request:
            provider = ScalewayDns("", "secret-key")
            self.assertTrue(provider.delete_dns_record("api.dev.example.com", "challenge-token"))

        changes = request.call_args_list[2].kwargs["json"]["changes"]
        self.assertEqual(changes, [{"delete": {"id": "wanted"}}])

    def test_domain_listing_and_record_mapping(self):
        responses = [
            zones_response(),
            FakeResponse({
                "total_count": 4,
                "records": [
                    {"id": "a", "name": "", "type": "A", "data": "192.0.2.1", "ttl": 300},
                    {"id": "mx", "name": "", "type": "MX", "data": "mail.example.net.",
                     "priority": 10, "ttl": 600},
                    {"id": "txt", "name": "www", "type": "TXT", "data": '"hello"', "ttl": 60},
                    {"id": "soa", "name": "", "type": "SOA", "data": "ignored", "ttl": 3600},
                ],
            }),
        ]
        with mock.patch.object(panel_dnsapi.requests, "request", side_effect=responses):
            records = ScalewayDns("", "secret-key").get_dns_record("example.com")

        self.assertEqual(records, [
            {"record": "@", "record_value": "192.0.2.1", "record_type": "A",
             "ttl": 300, "priority": -1, "proxy": -1},
            {"record": "@", "record_value": "mail.example.net.", "record_type": "MX",
             "ttl": 600, "priority": 10, "proxy": -1},
            {"record": "www", "record_value": "hello", "record_type": "TXT",
             "ttl": 60, "priority": -1, "proxy": -1},
        ])

    def test_domain_create_converts_fqdn_to_short_name(self):
        responses = [zones_response(), FakeResponse({"records": [{"id": "mx"}]})]
        with mock.patch.object(panel_dnsapi.requests, "request", side_effect=responses) as request:
            result = ScalewayDns("", "secret-key").create_org_record(
                "dev.example.com",
                "mail.dev.example.com",
                "mx.example.net.",
                "MX",
                1,
                priority=20,
            )

        self.assertTrue(result["status"])
        record = request.call_args_list[1].kwargs["json"]["changes"][0]["add"]["records"][0]
        self.assertEqual(record, {
            "name": "mail",
            "data": "mx.example.net.",
            "type": "MX",
            "ttl": 600,
            "priority": 20,
        })

    def test_domain_update_uses_atomic_set_by_remote_id(self):
        responses = [
            zones_response(),
            FakeResponse({
                "total_count": 1,
                "records": [{
                    "id": "remote-record-id",
                    "name": "www",
                    "type": "A",
                    "data": "192.0.2.1",
                    "ttl": 300,
                }],
            }),
            FakeResponse({"records": [{"id": "remote-record-id"}]}),
        ]
        with mock.patch.object(panel_dnsapi.requests, "request", side_effect=responses) as request:
            result = ScalewayDns("", "secret-key").update_record(
                "example.com",
                {"record": "www", "record_type": "A", "record_value": "192.0.2.1",
                 "ttl": 300, "priority": -1},
                {"record": "www", "record_type": "A", "record_value": "192.0.2.2",
                 "ttl": 300, "priority": -1},
            )

        self.assertTrue(result["status"])
        changes = request.call_args_list[2].kwargs["json"]["changes"]
        self.assertEqual(changes, [{"set": {
            "id": "remote-record-id",
            "records": [{
                "name": "www",
                "data": "192.0.2.2",
                "type": "A",
                "ttl": 300,
            }],
        }}])

    def test_invalid_token_has_actionable_error(self):
        response = FakeResponse({"message": "denied_authentication"}, status_code=403)
        with mock.patch.object(panel_dnsapi.requests, "request", return_value=response):
            with self.assertRaisesRegex(HintException, "DomainsDNSFullAccess"):
                ScalewayDns("", "bad-secret").verify()


if __name__ == "__main__":
    unittest.main()
