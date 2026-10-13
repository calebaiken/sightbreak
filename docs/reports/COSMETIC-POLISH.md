# Cosmetic experience stabilization

## Implemented

- Case reveal still receives only the server-committed item. Neutral sealed neighbours never depict fake alternate rarity outcomes. The committed result now receives a rifle silhouette, rarity colour and a brief settling highlight. Reduced motion and skip remain immediate and cannot change the reward.
- Item inspector and equipped weapons share deterministic collection palettes, pattern seed and wear material parameters. Inspection has improved fill/rim lighting, closer framing, handguard detail and reset view. Touch-generated mouse events are ignored to prevent doubled rotation.
- Reveal and inspection popups scroll vertically and remain bounded by safe landscape space. Tests cover 640×360, 896×414 and 1280×720 logical windows.
- A purchase/opening with an uncertain response retains its original endpoint, method and idempotency key in memory. Retry pending transaction sends the exact original body; other mutations wait until recovery. Recovery is scoped to the original account and server, and confirmed ownership is refreshed from the service.

## Verification

- Native economy widget regression passes, including skip-once semantics, reduced motion, inspector manipulation, emulated mouse rejection and all three landscape sizes.
- `game/tests/economy_recovery_test.gd`: 12 passing assertions for recovery and deterministic cosmetic materials.
- Actual OpenGL/Mesa native widget capture run exits without script errors or texture-leak reports. Captures in `.local/screenshots/economy-polish/` use explicitly fictional QA account/inventory fixtures; they are not earned player inventories.
- Added PostgreSQL regression cases for both ends of all six CSPRNG rarity ranges. Independent QA records their execution in the release report.
- Published weights remain 5800/2600/1100/400/90/10 out of 10,000 (58/26/11/4/0.9/0.1%). Economy service implementation and reward eligibility are unchanged. Online creation remains zero-value; only validated match rewards mint Credits, and marketplace proceeds transfer existing Credits. No payments, cash-out or real-money features exist. Challenge rewards remain unimplemented.

## Remaining limits

- Pending recovery survives screen changes within the running game, but is not persisted across process termination or explicit sign-out. The backend keeps idempotency receipts; a durable client recovery journal remains future work.
- Unkeyed trade/listing operations retain existing refresh-before-retry behaviour and server ownership/revision guards.
- Visual assessment and landscape tests are native desktop evidence, not physical phone touch/performance measurements. Inspector models remain original procedural geometry.
