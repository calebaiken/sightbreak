"""Independent pure pre-edit controls. No real target/module/kernel/Git calls."""
import ast
from copy import deepcopy
import hashlib
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import unittest

REPORT=Path(__file__).resolve().parents[1]
ACQUISITION=(REPORT/'frozen-acquisition.py').read_bytes()
OLD_TESTS=(REPORT/'frozen-old_tests.py').read_bytes()


def remove_only_added_readiness(raw):
    """Review prototype byte erasure, not a production protection patch."""
    tree=ast.parse(raw);classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LinuxKernel']
    if len(classes)!=1:raise ValueError('one LinuxKernel')
    methods=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='pidfd_alive']
    if len(methods)!=1 or methods[0] not in classes[0].body:raise ValueError('one in-class readiness method')
    method=methods[0]
    if not isinstance(method,ast.FunctionDef) or method.decorator_list:raise ValueError('undecorated normal method')
    args=method.args
    if args.posonlyargs or args.vararg or args.kwarg or args.kwonlyargs or args.defaults or [a.arg for a in args.args]!=['self','fd']:
        raise ValueError('exact readiness arguments')
    imports=[n for n in tree.body if isinstance(n,ast.Import) and any(a.name=='select' for a in n.names)]
    if len(imports)!=1 or len(imports[0].names)!=1 or imports[0].names[0].asname:raise ValueError('one unaliased select import')
    lines=raw.splitlines(keepends=True);imp=imports[0]
    if lines[imp.lineno-1]!=b'import select\n' or imp.end_lineno!=imp.lineno:raise ValueError('exact single import line')
    if method.col_offset!=4 or lines[method.lineno-1][:4]!=b'    ':raise ValueError('exact method indentation')
    # Whole physical new-method lines only; adjacent comments are never trimmed.
    if lines[method.end_lineno-1][method.end_col_offset:].strip():raise ValueError('unadmitted trailing bytes')
    ranges=[(sum(map(len,lines[:imp.lineno-1])),sum(map(len,lines[:imp.end_lineno]))),
            (sum(map(len,lines[:method.lineno-1])),sum(map(len,lines[:method.end_lineno])))]
    result=raw
    for start,end in sorted(ranges,reverse=True):result=result[:start]+result[end:]
    return result


def synthetic_addition(base=ACQUISITION):
    raw=base.replace(b'import selectors\n',b'import select\nimport selectors\n',1)
    tree=ast.parse(raw);kernel=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LinuxKernel')
    last=kernel.body[-1];lines=raw.splitlines(keepends=True);offset=sum(map(len,lines[:last.end_lineno]))
    # Body deliberately has no runtime implementation; it is parsed, never run.
    return raw[:offset]+b'    def pidfd_alive(self,fd):\n        return False\n'+raw[offset:]


def literal_function(name):
    node=next(n for n in ast.parse(ACQUISITION).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return deepcopy(node)


class SourceAndScopeControls(unittest.TestCase):
    def test_pinned_kernel_exit_semantics_are_not_zombie_reap_semantics(self):
        source=(REPORT/'pinned-source/exit.c').read_text()
        body=source.split('bool thread_group_exited(struct pid *pid)',1)[1].split('EXPORT_SYMBOL',1)[0]
        self.assertIn('exited = !task ||',body);self.assertIn('READ_ONCE(task->exit_state)',body);self.assertIn('thread_group_empty(task)',body)
        self.assertIn('all\n * threads are zombies, dead or completely gone',source)
        fork=(REPORT/'original-critic/kernel-model-source/fork.c').read_text()
        self.assertIn('poll_flags = EPOLLIN | EPOLLRDNORM;',fork)
        select=(REPORT/'pinned-source/select.c').read_text()
        self.assertIn('filter = demangle_poll(pollfd->events) | EPOLLERR | EPOLLHUP;',select);self.assertIn('mask &= filter;',select)

    def test_only_exact_added_method_and_import_reconstruct_all_original_bytes(self):
        self.assertEqual(remove_only_added_readiness(synthetic_addition()),ACQUISITION)
        self.assertEqual(hashlib.sha256(remove_only_added_readiness(synthetic_addition())).hexdigest(),hashlib.sha256(ACQUISITION).hexdigest())

    def test_missing_duplicate_decorated_async_and_outside_methods_reject(self):
        raw=synthetic_addition();method=b'    def pidfd_alive(self,fd):\n        return False\n'
        cases=[ACQUISITION,raw.replace(method,method+method),raw.replace(method,b'    @staticmethod\n'+method),
               raw.replace(method,method.replace(b'    def ',b'    async def ',1)),
               raw.replace(method,b'')+b'\ndef pidfd_alive(self,fd):\n    return False\n',
               raw.replace(method,method.replace(b'self,fd',b'self,fd,extra'))]
        for candidate in cases:
            with self.subTest(),self.assertRaises((ValueError,SyntaxError)):remove_only_added_readiness(candidate)

    def test_duplicate_aliased_combined_and_changed_imports_reject(self):
        raw=synthetic_addition()
        for replacement in (b'import select\nimport select\n',b'import select as aliased\n',b'import select, os\n',b'from select import poll\n',b'import select # outside bytes\n'):
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):remove_only_added_readiness(raw.replace(b'import select\n',replacement,1))

    def test_outside_comments_helpers_and_old_method_changes_survive_and_fail_hash(self):
        raw=synthetic_addition()
        for changed in (raw.replace(b'class OwnedTree:',b'# outside comment\nclass OwnedTree:',1),
                        raw+b'\ndef outside_helper():\n    return 1\n',
                        raw.replace(b'return os.waitpid(pid,os.WNOHANG)',b'return os.waitpid(pid,0)',1)):
            self.assertNotEqual(remove_only_added_readiness(changed),ACQUISITION)

    def test_old_zombie_reaper_loses_obligation_if_live_excludes_ready_entries(self):
        kernel_node=next(n for n in ast.parse(ACQUISITION).body if isinstance(n,ast.ClassDef) and n.name=='OwnedTree')
        method=deepcopy(next(n for n in kernel_node.body if isinstance(n,ast.FunctionDef) and n.name=='reap_descendants'))
        namespace={};exec(compile(ast.Module(body=[method],type_ignores=[]),'<literal-reaper>','exec'),namespace)
        calls=[];kernel=SimpleNamespace(supervisor=50,reap=lambda pid:(calls.append(pid) or (pid,0)))
        zombie=dict(pid=200,ppid=50,state='Z',start_ticks=1000)
        control=SimpleNamespace(root_pid=100,kernel=kernel,reaped=[],live=lambda:[zombie])
        namespace['reap_descendants'](control);self.assertEqual(calls,[200])
        calls.clear();control.live=lambda:[]  # readiness filter says exited, so not live.
        namespace['reap_descendants'](control);self.assertEqual(calls,[])
        self.assertEqual(zombie['state'],'Z')  # genuine owed reap was not performed.


class TimingConstructionControls(unittest.TestCase):
    def old_binding(self):
        clock=SimpleNamespace(now=100.)
        def now():return clock.now
        calls=[]
        def output(command,**options):
            calls.append(dict(command=command,timeout=options['timeout']));clock.now+=.1
            return 'a'*40 if options.get('text') else b''
        def run(command,**options):
            calls.append(dict(command=command,timeout=options['timeout']));clock.now+=.1;return SimpleNamespace(returncode=0)
        def require(ok,message):
            if not ok:raise RuntimeError(message)
        component=ast.literal_eval(next(n.value for n in ast.parse(ACQUISITION).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENT' for t in n.targets)))
        namespace=dict(time=SimpleNamespace(monotonic=lambda:None),subprocess=SimpleNamespace(check_output=output,run=run),
                       ROOT=PurePosixPath('/frozen'),COMPONENT=component,digest=lambda path:'b'*64,require=require)
        exec(compile(ast.Module(body=[literal_function('source_binding')],type_ignores=[]),'<literal-old-binding>','exec'),namespace)
        return namespace['source_binding'],clock,now,calls

    def test_literal_empty_git_construction_passes_old_four_calls_without_physical_proof(self):
        function,clock,now,calls=self.old_binding();result=function('a'*40,deadline=101.,clock=now)
        self.assertEqual(result['commit'],'a'*40);self.assertEqual(len(calls),4)
        self.assertTrue(all(0<row['timeout']<=1 for row in calls));self.assertEqual([r['timeout'] for r in calls],sorted([r['timeout'] for r in calls],reverse=True))
        self.assertTrue(all(sha=='b'*64 for sha in result['files'].values()))
        self.assertFalse(any('ls-tree' in row['command'] for row in calls))

    def test_late_original_budget_rejects_before_any_fake_git_query(self):
        function,clock,now,calls=self.old_binding();clock.now=101.
        with self.assertRaises(RuntimeError):function('a'*40,deadline=101.,clock=now)
        self.assertEqual(calls,[])

    def test_original_method_and_assertion_scope_are_frozen(self):
        source=json.loads((REPORT/'SOURCE_BINDING.json').read_bytes())
        raw=(REPORT/'original-timing-method.py.txt').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),source['timing']['sha256'])
        self.assertEqual(source['timing']['owner_class'],'SupervisorControls')
        method=ast.parse(b'class Holder:\n'+raw).body[0].body[0]
        assertions=[n for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]
        self.assertEqual(len(assertions),5)
        self.assertEqual(json.loads((REPORT/'frozen-protection.json').read_bytes())['old_tests_byte_erasure_sha256'],'44154d83d97c32ef688587f1f96190b6c880d306606792d85ad38fdce11b5978')

    def test_nul_tree_and_explicit_physical_fixture_can_supply_nonempty_proof(self):
        entries={'scripts/component.py':('100644',b'component'),
                 'scripts/import with\ttab\nand newline.py':('100755',b'imported dependency')}
        tree=b''.join(mode.encode()+b' blob '+hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest().encode()+b'\t'+name.encode()+b'\0' for name,(mode,data) in entries.items())
        parsed={}
        for row in tree.split(b'\0'):
            if not row:continue
            meta,name=row.split(b'\t',1);mode,kind,blob=meta.split()
            self.assertEqual(kind,b'blob');parsed[name.decode()]=(mode.decode(),blob.decode())
        self.assertEqual(set(parsed),set(entries))
        for name,(mode,data) in entries.items():self.assertEqual(parsed[name],(mode,hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()))
        self.assertEqual(len(b''.split(b'\0'))-1,0)  # old empty binary mock has no entries.


if __name__=='__main__':unittest.main()
