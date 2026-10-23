#!/usr/bin/env python3
"""Pure AX structural/privacy counterexamples; no native APIs, engine or OCR."""
import ast
import copy
import ctypes as C
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import macos_ax_contract as contract
import macos_ordinary_input as ordinary
from probe_macos_ax import BoundedObserver, NativeAX
import probe_macos_ax as observer
import verify_macos_ax_read_only as driver
from test_macos_ordinary import capture
from test_macos_capture_diagnostics import original_capture_helper


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'scripts/fixtures/macos_ax_read_only'


class FakeBackend:
    """Synthetic AX objects, never native receipts or actual semantic exposure."""
    def __init__(self):
        self.pid, self.window, self.bounds = 12, 34, [40, 60, 960, 568]
        self.now, self.until, self.calls = 10., 15., []
        self.objects = {
            'app': {'children': [0]},
            0: {'role': 'AXWindow', 'title': 'SIGHTBREAK (SYNTHETIC)', 'children': [1, 2, 3]},
            1: {'role': 'AXButton', 'title': 'DEPLOY   ·   OFFLINE 5V5', 'children': [],
                'enabled': True, 'frame': [100, 320, 350, 100]},
            2: {'role': 'AXTextField', 'children': [99]},
            3: {'role': 'AXStaticText', 'title': 'DO NOT READ STATIC ACCOUNT TEXT', 'children': []},
            99: {'role': 'AXStaticText', 'title': 'DO NOT READ TEXTFIELD CONTENTS', 'children': []}}

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    def guard(self):
        if self.now >= self.until:
            raise TimeoutError('Synthetic original deadline exceeded')
        return [{'owner_pid': self.pid, 'window_id': self.window, 'onscreen': True,
                 'bounds_points_including_chrome': list(self.bounds)}]

    def check_element(self, node):
        self.calls.append(('pid', node))
        if self.objects[node].get('pid', self.pid) != self.pid:
            raise RuntimeError('Synthetic wrong PID')

    def application(self):
        return 'app'

    def elements(self, node, name, limit):
        self.calls.append((name, node))
        values = self.objects[node]['children']
        if len(values) > limit:
            raise RuntimeError('Synthetic structural cap exceeded')
        return values

    def role(self, node):
        return self.objects[node]['role']

    def title(self, node):
        self.calls.append(('title', node))
        if self.role(node) not in ('AXWindow', 'AXButton'):
            raise AssertionError('Sensitive synthetic title read')
        return self.objects[node]['title']

    def frame(self, node):
        return self.objects[node].get('frame', list(self.bounds))

    def enabled(self, node):
        return self.objects[node]['enabled']

    def containing_window(self, node):
        return self.objects[node].get('window', 0)

    def same(self, left, right):
        return left == right


def observation(backend=None):
    backend = backend or FakeBackend()
    result = {'schema': contract.SCHEMA, 'nonce': 'a'*32, 'owner_pid': backend.pid,
              'window_id': backend.window, 'observer_pid': 999, 'AXIsProcessTrusted': True,
              'complete': False, 'caps': copy.deepcopy(contract.CAPS), 'snapshots': [],
              'examined_nodes': 0, 'input_events_posted': 0, 'permission_requests_made': 0,
              'api_call_counts': {'AXUIElementGetPid': 4},
              'coordinate_mapping': contract.MAPPING, 'started_monotonic': 10., 'finished_monotonic': 10.2}
    BoundedObserver(backend, result, clock=backend.clock, sleep=backend.sleep).observe()
    result['last_owned_layer_zero_rows'] = backend.guard()
    return result


def synthetic_capture():
    result = capture()
    result.update(owner_pid=12, input_events_posted=0, permission_requests_made=0,
                  bounds_points_including_chrome=[40,60,960,568], scwindow_frame_points=[40,60,960,568])
    result['text'][3]['confidence'] = .5
    return result


def validate(receipt, image=None, **changes):
    args = dict(pid=12, window=34, bounds=[40,60,960,568], nonce='a'*32,
                observer_pid=999, started=9.99, finished=10.3, budget=5.)
    args.update(changes)
    return contract.validate_observation(receipt, image or synthetic_capture(), **args)


class StructuralControls(unittest.TestCase):
    def test_valid_synthetic_exposure_preserves_original_point_eight_rejection(self):
        image, receipt = synthetic_capture(), observation()
        before = copy.deepcopy(image)
        result = validate(receipt, image)
        self.assertTrue(result['semantic_exposure_only'])
        self.assertFalse(result['gameplay_target_accepted'])
        self.assertEqual(image, before)
        with self.assertRaises(RuntimeError): ordinary.label_point(image, contract.LABEL)

    def test_textfield_subtree_and_static_text_titles_are_never_read(self):
        backend = FakeBackend(); receipt = observation(backend)
        self.assertEqual(receipt['examined_nodes'], 4)
        self.assertNotIn(('title', 2), backend.calls)
        self.assertNotIn(('title', 3), backend.calls)
        self.assertNotIn(('AXChildren', 2), backend.calls)
        self.assertNotIn(('pid', 99), backend.calls)
        self.assertNotIn('DO NOT READ', json.dumps(receipt))
        for role in contract.PRUNED_ROLES:
            backend=FakeBackend();backend.objects[2]['role']=role
            result=observation(backend)
            self.assertNotIn(('AXChildren',2),backend.calls)
            self.assertNotIn(('pid',99),backend.calls)
            self.assertNotIn('DO NOT READ',json.dumps(result))

    def test_wrong_pid_cycle_depth_and_node_exhaustion_fail_real_traversal(self):
        for fault in ('pid', 'cycle', 'depth', 'nodes'):
            backend = FakeBackend()
            if fault == 'pid': backend.objects[1]['pid'] = 13
            elif fault == 'cycle': backend.objects[3]['children'] = [0]
            elif fault == 'depth':
                backend.objects[0]['children'] = [10]
                for index in range(10,29):
                    backend.objects[index] = {'role':'AXGroup', 'children':[index+1] if index<28 else []}
            else: backend.objects[0]['children'] = list(range(1000))
            with self.subTest(fault=fault), self.assertRaises(RuntimeError): observation(backend)

    def test_three_empty_snapshots_share_original_clock_and_cumulative_node_cap(self):
        backend = FakeBackend(); backend.objects[0]['children'] = []
        result = observation(backend)
        self.assertFalse(result['complete'])
        self.assertEqual(len(result['snapshots']),3)
        self.assertEqual(result['examined_nodes'],3)
        self.assertAlmostEqual(backend.now,10.2)
        backend = FakeBackend(); backend.objects[0]['children'] = []
        backend.until = 10.15
        with self.assertRaises(TimeoutError): observation(backend)

    def test_cumulative_large_busy_trees_and_serialized_byte_ceiling_cannot_reset(self):
        backend=FakeBackend();backend.objects[0]['children']=list(range(10,109))
        for index in range(10,109):backend.objects[index]={'role':'AXGroup','children':[]}
        with self.assertRaises(RuntimeError):observation(backend)
        backend=FakeBackend();backend.objects[0]['children']=list(range(10,250))
        for index in range(10,250):
            backend.objects[index]={'role':'AXButton','title':'\\'*512,'enabled':True,'children':[],
                                    'frame':[100,320,350,100]}
        result={'snapshots':[],'examined_nodes':0,'complete':False}
        observer=BoundedObserver(backend,result,clock=backend.clock,sleep=backend.sleep)
        with self.assertRaisesRegex(RuntimeError,'byte ceiling'):observer.observe()
        self.assertLess(len(json.dumps(result,ensure_ascii=False).encode()),contract.CAPS['receipt_bytes'])
        self.assertFalse(result['complete'])
        self.assertGreater(result['examined_nodes'],1)

    def test_stale_snapshot_private_call_or_spoofed_parent_window_identity_reject(self):
        for fault in ('stale_snapshot','api','parent','pruned_child','bool_node','bool_depth','window_pid','window_role'):
            receipt=observation();snapshot=receipt['snapshots'][0]
            if fault=='stale_snapshot':snapshot['started_monotonic']=0
            elif fault=='api':receipt['api_call_counts']['AXUIElementPerformAction']=1
            elif fault=='parent':snapshot['nodes'][1]['parent']=99
            elif fault=='pruned_child':snapshot['nodes'][3].update(parent=2,depth=2)
            elif fault=='bool_node':snapshot['nodes'][1]['node']=True
            elif fault=='bool_depth':snapshot['nodes'][1]['depth']=True
            elif fault=='window_pid':snapshot['windows'][0]['pid']=13
            else:snapshot['windows'][0]['role']='AXGroup'
            with self.subTest(fault=fault),self.assertRaises(RuntimeError):validate(receipt)

    def test_window_duplicates_foreign_containing_window_and_geometry_disagreement_fail(self):
        for fault in ('window', 'frame', 'containing'):
            backend = FakeBackend()
            if fault == 'window': backend.objects['app']['children'] = [0,0]
            if fault == 'frame': backend.objects[0]['frame'] = [0,0,999,999]
            if fault == 'containing': backend.objects[1]['window'] = 3
            with self.subTest(fault=fault), self.assertRaises(RuntimeError): observation(backend)

    def test_exact_title_words_role_enabled_duplicate_and_bounded_frame(self):
        for fault in ('words','order','extra','punctuation','case','role','disabled','duplicate','outside','nan','zero','large_title'):
            receipt = observation(); button = receipt['snapshots'][-1]['nodes'][1]
            if fault in ('words','order','extra','punctuation','case','large_title'):
                text = {'words':'DEPLOY · ONLINE 5V5','order':'OFFLINE 5V5 · DEPLOY','extra':'DEPLOY · OFFLINE 5V5 NOW',
                        'punctuation':'DEPLOY - OFFLINE 5V5','case':'Deploy · OFFLINE 5V5','large_title':'x'*513}[fault]
                button['title'] = text
                if fault!='large_title': button['normalized_title'] = contract.normalized_title(text)
            elif fault=='role': button['role']='AXStaticText'
            elif fault=='disabled': button['enabled']=False
            elif fault=='duplicate':
                other=dict(button,node=100)
                receipt['snapshots'][-1]['nodes'].append(other);receipt['examined_nodes']+=1
            elif fault=='outside': button['frame_points']=[-5,-5,10,10]
            elif fault=='nan': button['frame_points'][0]=float('nan')
            else: button['frame_points'][2]=0
            with self.subTest(fault=fault), self.assertRaises(RuntimeError): validate(receipt)
        receipt=observation();button=receipt['snapshots'][-1]['nodes'][1]
        button['title']='DEPLOY • OFFLINE 5V5';button['normalized_title']=contract.normalized_title(button['title'])
        self.assertTrue(validate(receipt)['unique_semantic_candidate'])

    def test_owner_window_nonce_trust_stale_time_caps_and_raw_context_reject(self):
        for key,value in [('owner_pid',13),('window_id',35),('nonce','b'*32),('observer_pid',1000),
                          ('AXIsProcessTrusted',False),('complete',False),('input_events_posted',1),
                          ('permission_requests_made',1),('started_monotonic',9.),('finished_monotonic',16.),
                          ('coordinate_mapping','guessed Retina flip')]:
            receipt=observation();receipt[key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):validate(receipt)
        for fault in ('pid','window','mapping','anchors','duplicate','wrong_text','frame','privacy','nodes','depth'):
            receipt,image=observation(),synthetic_capture()
            if fault=='pid': image['owner_pid']=13
            elif fault=='window': image['window_id']=99
            elif fault=='mapping': image['point_pixel_scale']=True
            elif fault=='anchors': image['text'][0]['confidence']=.799
            elif fault=='duplicate': image['text'].append(copy.deepcopy(image['text'][3]))
            elif fault=='wrong_text': image['text'][3]['text']='DEPLOY · ONLINE 5V5'
            elif fault=='frame': receipt['snapshots'][-1]['nodes'][1]['frame_points']=[45,65,20,20]
            elif fault=='privacy': receipt['snapshots'][-1]['nodes'][2]['AXValue']='sensitive'
            elif fault=='nodes': receipt['examined_nodes']=257
            elif fault=='depth': receipt['snapshots'][-1]['nodes'][1]['depth']=17
            with self.subTest(fault=fault),self.assertRaises(RuntimeError):validate(receipt,image)

    def test_every_current_cg_row_set_rejects_late_extra_window_or_pinned_change(self):
        for key in ('cg_before','cg_after'):
            for fault in ('duplicate','owner','id','bounds'):
                receipt=observation();rows=receipt['snapshots'][-1][key]
                if fault=='duplicate':rows.append(dict(rows[0],window_id=55))
                elif fault=='owner':rows[0]['owner_pid']=13
                elif fault=='id':rows[0]['window_id']=55
                else:rows[0]['bounds_points_including_chrome'][2]+=1
                with self.subTest(key=key,fault=fault),self.assertRaises(RuntimeError):validate(receipt)
        receipt=observation();rows=receipt['last_owned_layer_zero_rows']
        rows.append(dict(rows[0],window_id=55))
        with self.assertRaises(RuntimeError):validate(receipt)

    def test_actual_attribute_gate_rejects_private_account_value_and_text_reads(self):
        reader=NativeAX.__new__(NativeAX)
        for name in ('AXValue','AXSelectedText','AXDescription','AXHelp','AXIdentifier','_AXUIElementGetWindow','AXTitleUIElement'):
            with self.subTest(name=name),self.assertRaises(RuntimeError):reader.key(name)
        self.assertEqual(contract.ATTRIBUTES,('AXRole','AXChildren','AXWindows','AXTitle','AXPosition','AXSize','AXEnabled','AXWindow'))

    def test_actual_reader_methods_fail_before_any_sensitive_string_or_private_call(self):
        reader=NativeAX.__new__(NativeAX)
        reader.role=lambda _: 'AXTextField'
        with self.assertRaises(RuntimeError):reader.title(1)
        with self.assertRaises(RuntimeError):reader.string(1,'AXValue')
        with self.assertRaises(RuntimeError):reader.elements(1,'AXSelectedText',2)
        with self.assertRaises(RuntimeError):reader.call('AXUIElementPerformAction',1,2)

    def test_actual_native_call_rejects_late_success_and_changed_window(self):
        reader=NativeAX.__new__(NativeAX)
        reader.calls={}
        reader.ax=type('SyntheticFunctions',(),{'AXUIElementGetPid':staticmethod(lambda *_:0)})()
        checks=[]
        def guard():
            checks.append(1)
            if len(checks)>1:raise TimeoutError('Synthetic late return')
        reader.guard=guard
        with self.assertRaises(TimeoutError):reader.call('AXUIElementGetPid',1,2)
        self.assertEqual(reader.calls,{'AXUIElementGetPid':1})


def boundary_reader():
    """Real adapter with fake C endpoints only; no libraries are constructed."""
    reader=NativeAX.__new__(NativeAX)
    reader.pid,reader.window,reader.bounds=12,34,[40,60,960,568]
    reader.calls,reader.refs,reader.keys,reader.latest_rows={ },[],{ },[]
    reader.deadline=15.
    reader.released,reader.retained=[],[]
    reader.rows=[{'owner_pid':12,'window_id':34,'onscreen':True,
                  'bounds_points_including_chrome':[40,60,960,568]}]
    reader.windows=lambda _pid:copy.deepcopy(reader.rows)
    def retain(value):
        reader.retained.append(value)
        return value
    reader.cf=SimpleNamespace(CFRelease=reader.released.append,CFRetain=retain,
        CFGetTypeID=lambda _:7,CFArrayGetTypeID=lambda:7,CFArrayGetCount=lambda _:1,
        CFArrayGetValueAtIndex=lambda *_:0xB44)
    return reader


class NativeBoundaryControls(unittest.TestCase):
    def test_actual_call_elapsed_bound_rejects_point_two_five_without_renewing_whole_deadline(self):
        for elapsed,accepted in ((0.,True),(.249,True),(.25,False),(.300,False),(5.001,False)):
            with self.subTest(elapsed=elapsed):
                reader,now=boundary_reader(),[10.]
                def native(*_arguments):now[0]+=elapsed;return 0
                reader.ax=SimpleNamespace(AXUIElementGetPid=native)
                with patch.object(observer.time,'monotonic',lambda:now[0]):
                    if accepted:self.assertEqual(reader.call('AXUIElementGetPid',1,None),0)
                    else:
                        with self.assertRaises(TimeoutError):reader.call('AXUIElementGetPid',1,None)
                self.assertEqual(reader.deadline,15.)
                self.assertEqual(reader.calls,{'AXUIElementGetPid':1})

    def test_create_and_copy_plus_one_references_survive_post_call_rejection_and_native_error(self):
        for kind,pointer in (('application',0xA11),('attribute',0xA22),('array',0xA33)):
            for fault in ('none','call_late','whole_late','window','native_error','native_exception'):
                if kind=='application' and fault in ('native_error','native_exception'):continue
                with self.subTest(kind=kind,fault=fault):
                    reader,now=boundary_reader(),[10.]
                    reader.check_element=lambda _element:None
                    reader.key=lambda name:name
                    def finish():
                        if fault=='call_late':now[0]+=.300
                        elif fault=='whole_late':now[0]+=5.001
                        elif fault=='window':reader.rows.append(dict(reader.rows[0],window_id=35))
                        elif fault=='native_exception':raise RuntimeError('Synthetic native boundary exception')
                        return -25205 if fault=='native_error' else 0
                    def copied(*arguments):
                        arguments[-1]._obj.value=pointer
                        return finish()
                    def created(_pid):finish();return pointer
                    def count(_element,_key,output):output._obj.value=1;return 0
                    reader.ax=SimpleNamespace(AXUIElementCreateApplication=created,
                        AXUIElementCopyAttributeValue=copied,AXUIElementGetAttributeValueCount=count,
                        AXUIElementCopyAttributeValues=copied)
                    operation={'application':lambda:reader.application(),'attribute':lambda:reader.attribute(1,'AXRole'),
                               'array':lambda:reader.elements(1,'AXChildren',4)}[kind]
                    with patch.object(observer.time,'monotonic',lambda:now[0]):
                        if fault=='none':operation()
                        else:
                            with self.assertRaises((RuntimeError,TimeoutError)):operation()
                    reader.close()
                    self.assertEqual(reader.released.count(pointer),1)
                    self.assertEqual(reader.refs,[])
                    if kind=='array' and fault=='none':
                        self.assertEqual(reader.retained,[0xB44])
                        self.assertEqual(reader.released,[0xB44,0xA33])

    def test_copy_array_wrong_type_count_or_null_child_preserves_array_cleanup(self):
        for fault in ('type','count','null_child'):
            with self.subTest(fault=fault):
                reader=boundary_reader();reader.check_element=lambda _element:None;reader.key=lambda name:name
                def count(_element,_key,output):output._obj.value=1;return 0
                def copied(_element,_key,_start,_count,output):output._obj.value=0xA33;return 0
                reader.ax=SimpleNamespace(AXUIElementGetAttributeValueCount=count,AXUIElementCopyAttributeValues=copied)
                if fault=='type':reader.cf.CFGetTypeID=lambda _:8
                elif fault=='count':reader.cf.CFArrayGetCount=lambda _:2
                else:reader.cf.CFArrayGetValueAtIndex=lambda *_:None
                with patch.object(observer.time,'monotonic',lambda:10.):
                    with self.assertRaises(RuntimeError):reader.elements(1,'AXChildren',4)
                reader.close()
                self.assertEqual(reader.released,[0xA33])

    def test_reference_limit_or_registry_failure_releases_owned_but_not_borrowed_pointers(self):
        for retained in (False,True):
            reader=boundary_reader();reader.refs=list(range(0xD00,0xD00+2048))
            with self.assertRaises(RuntimeError):reader.hold(0xA22,retained=retained)
            self.assertEqual(reader.retained,[])
            self.assertEqual(reader.released,[0xA22] if retained else [])
            reader.close()
            self.assertEqual(reader.released.count(0xA22),int(retained))
        class BrokenRegistry(list):
            def append(self,_value):raise MemoryError('Synthetic append failure')
        for retained in (False,True):
            reader=boundary_reader();reader.refs=BrokenRegistry()
            with self.assertRaises(MemoryError):reader.hold(0xA22,retained=retained)
            reader.close()
            self.assertEqual(reader.released,[0xA22])
        reader=boundary_reader();reader.refs=list(range(0xD00,0xD00+2048))
        reader.cf.CFStringCreateWithCString=lambda *_:0xA44
        with self.assertRaises(RuntimeError):reader.key('AXRole')
        self.assertNotIn('AXRole',reader.keys)
        reader.close()
        self.assertEqual(reader.released.count(0xA44),1)

    @staticmethod
    def string_reader(title=None,*,raw=None,units=None,conversion_ok=True):
        reader=boundary_reader()
        if raw is None:raw=title.encode('utf-8')
        if units is None:units=len(title.encode('utf-16-le'))//2
        reader.role=lambda _element:'AXButton'
        reader.attribute=lambda *_arguments:1
        def converted(_value,buffer,capacity,_encoding):
            if not conversion_ok or len(raw)+1>capacity:return False
            C.memmove(buffer,raw+b'\0',len(raw)+1)
            return True
        reader.cf=SimpleNamespace(CFGetTypeID=lambda _:7,CFStringGetTypeID=lambda:7,
            CFStringGetLength=lambda _:units,CFStringGetCString=converted)
        return reader

    def test_complete_counted_native_strings_preserve_utf8_non_bmp_and_exact_byte_boundary(self):
        for title in ('','SIGHTBREAK (DEBUG)','DEPLOY   ·   OFFLINE 5V5','DEPLOY • OFFLINE 5V5',
                      'é'*256,'🙂'*128,'a'*512,'e\u0301'*170):
            with self.subTest(title=title[:24]):
                self.assertEqual(self.string_reader(title).title(1),title)
        backend=FakeBackend();backend.objects[1]['title']=self.string_reader('DEPLOY   ·   OFFLINE 5V5').title(1)
        self.assertTrue(validate(observation(backend))['unique_semantic_candidate'])

    def test_native_nul_control_and_trailing_nul_cannot_become_exact_deploy(self):
        label=contract.LABEL
        titles=[label+'\0DIFFERENT TITLE',label+'\0',label+'\0\0','\0'+label,'\0']
        titles+=['DEPLOY'+char+' · OFFLINE 5V5' for char in ('\x01','\t','\n','\r','\x7f','\x85')]
        for title in titles:
            with self.subTest(title=repr(title)):
                with self.assertRaises(RuntimeError):
                    backend=FakeBackend();backend.objects[1]['title']=self.string_reader(title).title(1)
                    validate(observation(backend))
                with self.assertRaises(RuntimeError):contract.normalized_title(title)

    def test_string_bad_utf8_count_conversion_failure_and_oversize_fail_without_prefix_acceptance(self):
        readers=[self.string_reader(raw=b'\xff',units=1),self.string_reader(raw=b'\xed\xa0\x80',units=1),
                 self.string_reader('DEPLOY · OFFLINE 5V5',units=1),self.string_reader('a'*513),
                 self.string_reader('é'*257),self.string_reader('DEPLOY · OFFLINE 5V5',conversion_ok=False)]
        for reader in readers:
            with self.assertRaises(RuntimeError):reader.title(1)
        with self.assertRaises(RuntimeError):contract.normalized_title('\ud800')

    def test_owned_string_type_length_conversion_and_control_failures_release_original_copy(self):
        for fault in ('type','length','conversion','utf8','nul'):
            with self.subTest(fault=fault):
                reader=boundary_reader();reader.check_element=lambda _element:None;reader.key=lambda name:name
                reader.role=lambda _element:'AXButton'
                def copied(_element,_key,output):output._obj.value=0xA22;return 0
                reader.ax=SimpleNamespace(AXUIElementCopyAttributeValue=copied)
                raw=b'x\0y' if fault=='nul' else b'\xff' if fault=='utf8' else b'x'
                reader.cf.CFStringGetTypeID=lambda:8 if fault=='type' else 7
                reader.cf.CFStringGetLength=lambda _pointer:513 if fault=='length' else len(raw)
                def converted(_pointer,buffer,_capacity,_encoding):
                    if fault=='conversion':return False
                    C.memmove(buffer,raw+b'\0',len(raw)+1)
                    return True
                reader.cf.CFStringGetCString=converted
                with patch.object(observer.time,'monotonic',lambda:10.):
                    with self.assertRaises(RuntimeError):reader.title(1)
                reader.close()
                self.assertEqual(reader.released,[0xA22])


class SourceControls(unittest.TestCase):
    def test_declared_union_reconstructs_original_helper_selector_hud_and_runtime_sources(self):
        fixture=json.loads((FIXTURES/'preserved-source.json').read_text())
        for path,digest in fixture['sha256'].items():
            data=(ROOT/path).read_bytes()
            if path=='scripts/macos_window_capture.swift':
                data=original_capture_helper(data)
            elif path in ('scripts/macos_ordinary_input.py', 'scripts/verify_macos_ordinary.py'):
                # This union explicitly adds the ordinary semantic route. The
                # independent new source controls bind its exact delta/defaults.
                from test_macos_semantic_deploy import original_ordinary_source
                data=original_ordinary_source(path, data)
            elif path=='scripts/native_log.py':
                # Exact accepted root db9d305f has the newer strict StringName
                # guard; importing an older diagnostic must not overwrite it.
                digest='8684252c3ec4ca466fe24a31f938a7614b8ce993c91041b0a2c42d2d483f94e1'
            with self.subTest(path=path):self.assertEqual(hashlib.sha256(data).hexdigest(),digest)

    def test_new_native_sources_have_only_declared_read_api_and_appkit_selectors(self):
        allowed={'AXUIElementCreateApplication','AXUIElementGetTypeID','AXUIElementGetPid',
                 'AXUIElementSetMessagingTimeout','AXUIElementCopyAttributeValue',
                 'AXUIElementGetAttributeValueCount','AXUIElementCopyAttributeValues',
                 'AXValueGetTypeID','AXValueGetType','AXValueGetValue'}
        tree=ast.parse((ROOT/'scripts/probe_macos_ax.py').read_text())
        names={node.attr for node in ast.walk(tree) if isinstance(node,ast.Attribute) and node.attr.startswith('AX')}
        literals={node.value for node in ast.walk(tree) if isinstance(node,ast.Constant) and isinstance(node.value,str)
                  and node.value.startswith(('AXUIElement','AXValueGet'))}
        self.assertLessEqual(names|literals,allowed)
        for filename in ('probe_macos_ax.py','macos_ax_appkit.py','verify_macos_ax_read_only.py'):
            source=(ROOT/'scripts'/filename).read_text()
            for forbidden in ('CGEventCreate','CGEventPost(', 'AXUIElementPerformAction', 'AXUIElementSetAttributeValue',
                              'AXIsProcessTrustedWithOptions','AXUIElementCreateSystemWide','_AXUIElementGetWindow'):
                self.assertNotIn(forbidden,source)

    def test_launch_amendment_and_original_finite_caps(self):
        args=driver.launch_arguments('/exact/SIGHTBREAK','/exact/trace')
        self.assertEqual(args,['/exact/SIGHTBREAK','--audio-driver','Dummy','--log-file','user://mac-ordinary-engine.log',
            '--windowed','--resolution','1280x720','--position','40,60','--accessibility','always','--',
            '--offline-validation','--offline-trace-dir=/exact/trace'])
        self.assertEqual(contract.CAPS,{'seconds':5,'snapshots':3,'spacing_seconds':.1,'call_seconds':.25,
            'depth':16,'nodes':256,'receipt_bytes':524288,'title_bytes':512})
        self.assertEqual(driver.BUDGETS['total'],300)
        self.assertEqual(driver.BUDGETS['compile'],60)

    def test_ordinary_source_union_keeps_the_exact_accepted_root_workflow(self):
        # This source experiment imports no diagnostic workflow or dispatch lane.
        current=(ROOT/'.github/workflows/desktop-alpha.yml').read_bytes()
        original=(ROOT/'scripts/fixtures/macos_semantic_deploy/desktop-alpha-base.yml.txt').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         '5b662868c7cdc80f77ebb8c6767ff1d6b983a81870e668effabe95bd1cdde075')
        self.assertEqual(current,original)


if __name__=='__main__':unittest.main()
