# Transfer receipt

The GitHub connector returned supported artifact file_uri references. An initial
attempt to read its signed download_url through the inherited workspace proxy
failed with `OSError: Tunnel connection failed: 403 Forbidden`. No artifact
bytes were written and the denied URL was not retried.

The prior native outcome critic confirmed these connector file_uri.file_id
values are Sediment-backed workspace transfers, as used for the prior ARM and
Linux artifacts. The supported `download_file` tool then succeeds for both
official artifacts; local hashes/sizes match GitHub metadata. No proxy setting,
credential, security identity or host policy was changed.

- Full-QA file_id: file_0000000085e081f5ac3be8ab28962552; 1,410,807 bytes.
- Receipts file_id: file_000000003cd081f59a540992ea59e316; 1,628,280 bytes.
- Inner original qa-receipts.zip: 1,628,136 bytes, SHA256
  2cdd28b261efd56f673cb6a15171011458f4ed0c8584e3713ada4e7601124be1.

Signed URLs are temporary transport capabilities and are omitted from this
permanent report. Both connector artifact originals are preserved under archives.
