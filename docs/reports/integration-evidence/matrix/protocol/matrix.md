| Client | Server | Expected | Observed | Result | Last message shown to the player |
| --- | --- | --- | --- | --- | --- |
| 0.3.0 (e67f2c8) | 0.3.0 (e67f2c8) | join | joined after 0.46 s | PASS | Cipher  ›  Morrow |
| this branch (protocol 5) | this branch (protocol 5) | join | joined after 0.23 s | PASS | Echo  ›  Sable |
| 0.3.0 (e67f2c8) | this branch (protocol 5) | server drops pre-handshake client | never admitted; dropped 3x by the server, first after 5.3 s; 0.3.0 client retries on its own | PASS | Connecting to Relay Yard… |
| this branch (protocol 5) | 0.3.0 (e67f2c8) | client reports missing handshake | failed after 5.2 s, no retries | PASS | No version handshake from the server within 5 seconds. It is probably running an older SIGHTBREAK release (0.3.0 has no handshake) or is not a SIGHTBREAK server. Join a server running the same version as this client. |
| next build (protocol 6) | this branch (protocol 5) | explicit mismatch | rejected after 0.3 s with the reason shown | PASS | Version mismatch: this client uses SIGHTBREAK network protocol 6. This server uses network protocol 5; this client sent protocol 6. Install the same SIGHTBREAK version as the server to join. |
| this branch (protocol 5) | next build (protocol 6) | explicit mismatch | rejected after 0.1 s with the reason shown | PASS | Version mismatch: this client uses SIGHTBREAK network protocol 5. This server uses network protocol 6; this client sent protocol 5. Install the same SIGHTBREAK version as the server to join. |
