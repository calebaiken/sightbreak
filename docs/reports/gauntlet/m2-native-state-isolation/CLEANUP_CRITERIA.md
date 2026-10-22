# Cleanup receipt correction

Declared before the follow-up implementation. Independent critic
`/root/native_isolation_critic` reproduced a false passing receipt on isolation
candidate `1195b23423b4cb37c613e9e0304508d4c2637aff`:
real native peer-lifecycle success followed by injected namespace cleanup
`PermissionError` left `passed=true`, `failure=null`, `cleanup=[]` and the owned
namespace present. The process itself failed. Original critic evidence:
`/workspace/reviews/m2-isolation-critic/cleanup-failure-observed.json` and
`cleanup_failure_control.py`.

Required correction:

1. Every registered namespace records an attempted removal, including failures.
   No empty-list or partial-cleanup result may certify success.
2. Namespace failure still attempts temporary-project cleanup. Temporary cleanup
   failure also produces a failing receipt with its actual error.
3. Original native exceptions remain the primary propagated failure if cleanup
   also fails. Record the additional failure without hiding either error.
4. Resource-inventory failures still attempt cleanup and produce a failing
   receipt. Successful native runs and cleanup retain their passing behavior.
5. Exercise these paths using actual native peer-lifecycle output, real owned
   directories and scoped fault injection. Include an actual failing native
   subprocess for the combined-failure case, not a fabricated success/failure.
6. Preserve source identity, save guards, suite list and watchdogs. Cross-platform
   acceptance remains pending native-host CI; builder acceptance is prohibited.
