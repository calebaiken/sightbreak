"""Independent source-only falsifiers; no native, SQL, socket or HTTP runtime."""
import argparse
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

candidate = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(candidate / "scripts"))
import test_postgres_receipt_recovery as campaign
from postgres_receipt_oracle import verify_market
from test_postgres_receipt_oracle import fixture


class IndependentFindings(unittest.TestCase):
    def test_changed_response_metadata_cannot_hide_in_matching_operation(self):
        before, settled, spec, response = fixture()
        response["item"]["pattern_seed"] += 1
        settled["business"]["operations"][0]["response"] = deepcopy(response)
        with self.assertRaises(AssertionError):
            verify_market(before, settled, spec, response)

    def test_wrong_route_refused_mutation_is_still_observed(self):
        with tempfile.TemporaryDirectory(prefix="receipt-independent-pure-") as directory:
            args = argparse.Namespace(out=Path(directory) / "output", godot=Path(directory) / "unused", component="market")
            run = campaign.Run(args)
            run.spec = {"path": "/market/expected-listing/buy"}
            handler = object.__new__(run.proxy_handler("pure-origin"))
            body = json.dumps({"idempotency_key": "pure-UUID", "expected_price": 400}).encode()
            handler.command, handler.path = "POST", "/market/other-listing/buy"
            handler.headers = {"Content-Length": str(len(body))}
            handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
            handler.send_response = mock.Mock()
            handler.send_header = mock.Mock()
            handler.end_headers = mock.Mock()
            backend = mock.Mock(status=409)
            backend.read.return_value = b'{"detail":"Listing unavailable"}'
            backend.getheader.return_value = "application/json"
            connection = mock.Mock()
            connection.getresponse.return_value = backend
            with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection), \
                 mock.patch.object(campaign.subprocess, "Popen", side_effect=AssertionError("native runtime forbidden")), \
                 mock.patch.object(campaign.socket, "socket", side_effect=AssertionError("socket runtime forbidden")), \
                 mock.patch.object(campaign, "ThreadingHTTPServer", side_effect=AssertionError("server runtime forbidden")):
                handler.forward()
            self.assertTrue(connection.request.called)
            recorded = [row for row in run.events if row.get("path") == handler.path and row.get("raw_body_hex") == body.hex()]
            self.assertTrue(recorded, "wrong-route mutation was forwarded but omitted from retained request evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)
