"""Pure owned-process edge tests; no real child, pidfd or signal is used."""
import unittest
import ast
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import acquire_fov_math_reference as acquisition
from test_fov_math_reference import FakeKernel
from test_fov_binary_input import erase_ancestry_class,ancestry_baseline_segments


def child(pid,parent,birth):
    return dict(pid=pid,state='R',ppid=parent,pgrp=100,session=100,start_ticks=birth)


class OwnedAncestryControls(unittest.TestCase):
    def tree(self,kernel):
        tree=acquisition.OwnedTree(kernel,100);tree.bind_root();self.addCleanup(tree.close)
        return tree

    def test_stale_child_number_with_unrelated_parent_is_never_bound_or_signaled(self):
        kernel=FakeKernel();kernel.table[200]=child(200,999,456)
        kernel.children=lambda pid:[100,200] if pid==50 else []
        tree=self.tree(kernel)
        with self.assertRaisesRegex(RuntimeError,'ancestry'):tree.observe()
        self.assertNotIn(200,[v['identity']['pid'] for v in tree.seen.values()])
        tree.signal_all(15)
        self.assertIn(200,kernel.table);self.assertFalse(any(pid==200 for pid,_ in kernel.sent))

    def test_queued_parent_reuse_during_enumeration_cannot_import_its_new_child(self):
        kernel=FakeKernel();kernel.table.update({200:child(200,100,456),300:child(300,200,789)})
        def children(pid):
            if pid==50:return[100]
            if pid==100:return[200]
            if pid==200:
                kernel.table[200].update(ppid=999,start_ticks=457)
                return[300]
            return[]
        kernel.children=children;tree=self.tree(kernel)
        with self.assertRaisesRegex(RuntimeError,'parent birth'):tree.observe()
        self.assertNotIn(300,[v['identity']['pid'] for v in tree.seen.values()])
        tree.signal_all(15)
        self.assertTrue({200,300}<=set(kernel.table))
        self.assertFalse(any(pid in (200,300) for pid,_ in kernel.sent))

    def test_reused_queued_parent_is_checked_before_its_children_are_requested(self):
        kernel=FakeKernel();kernel.table[200]=child(200,100,456)
        original_identity=kernel.identity;reads=0;enumerated=[]
        def identity(pid):
            nonlocal reads
            if pid==200:
                reads+=1
                if reads==3:kernel.table[200].update(ppid=999,start_ticks=457)
            return original_identity(pid)
        original_children=kernel.children
        def children(pid):enumerated.append(pid);return original_children(pid)
        kernel.identity=identity;kernel.children=children;tree=self.tree(kernel)
        with self.assertRaisesRegex(RuntimeError,'parent birth'):tree.observe()
        self.assertNotIn(200,enumerated)

    def test_child_reparent_during_pidfd_open_closes_unproven_handle(self):
        kernel=FakeKernel();kernel.table[200]=child(200,100,456)
        original=kernel.open_pid
        def opening(pid):
            fd=original(pid)
            if pid==200:kernel.table[pid]['ppid']=999
            return fd
        kernel.open_pid=opening;tree=self.tree(kernel)
        with self.assertRaisesRegex(RuntimeError,'ancestry'):tree.observe()
        self.assertIn(200,kernel.closed);self.assertNotIn((200,456),tree.seen)
        tree.signal_all(15);self.assertFalse(any(pid==200 for pid,_ in kernel.sent))

    def test_parent_death_during_pidfd_open_does_not_establish_an_edge(self):
        kernel=FakeKernel();kernel.table[200]=child(200,100,456)
        original=kernel.open_pid
        def opening(pid):
            fd=original(pid)
            if pid==200:kernel.table.pop(100)
            return fd
        kernel.open_pid=opening;tree=self.tree(kernel)
        with self.assertRaisesRegex(RuntimeError,'ancestry'):tree.observe()
        self.assertIn(200,kernel.closed);self.assertNotIn((200,456),tree.seen)
        tree.signal_all(15);self.assertFalse(kernel.sent)

    def test_current_supervisor_can_adopt_its_reparented_owned_orphan(self):
        kernel=FakeKernel();kernel.table[200]=child(200,100,456);tree=self.tree(kernel)
        tree.observe();first_handle=tree.seen[(200,456)]['fd']
        kernel.table.pop(100);kernel.table[200]['ppid']=50
        tree.observe()
        self.assertEqual(tree.seen[(200,456)]['fd'],first_handle)
        tree.signal_all(15)
        self.assertIn((200,15),kernel.sent);self.assertFalse(any(pid==50 for pid,_ in kernel.sent))

    def test_supervisor_birth_change_blocks_traversal_and_signals(self):
        kernel=FakeKernel();tree=self.tree(kernel);kernel.supervisor_birth+=1
        with self.assertRaisesRegex(RuntimeError,'supervisor birth'):tree.observe()
        with self.assertRaisesRegex(RuntimeError,'supervisor birth'):tree.signal_all(15)
        self.assertFalse(kernel.sent)

    def test_unchanged_three_generation_tree_keeps_all_and_only_owned_births(self):
        kernel=FakeKernel();kernel.table.update({200:child(200,100,456),300:child(300,200,789),999:child(999,999,900)})
        tree=self.tree(kernel);tree.observe()
        self.assertEqual(set(tree.seen),{(100,123),(200,456),(300,789)})
        tree.signal_all(15)
        self.assertEqual({pid for pid,_ in kernel.sent},{100,200,300})
        self.assertIn(999,kernel.table)


class AncestryProtectionControls(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]
        raw=(root/'scripts/acquire_fov_math_reference.py').read_bytes()
        self.process=raw[raw.index(b'class LinuxKernel:'):raw.index(b'def acquire(')]
        self.baseline=ancestry_baseline_segments()['owned_tree']['text'].encode()
        self.expected=json.loads((root/'scripts/fixtures/fov_binary_protected_segments.json').read_text())['process_classes']['sha256']

    def digest(self,raw):
        return hashlib.sha256(erase_ancestry_class(raw,'OwnedTree',self.baseline)).hexdigest()

    def test_exact_scoped_reconstruction_keeps_original_process_hash(self):
        self.assertEqual(self.digest(self.process),self.expected)

    def test_adjacent_comments_helpers_and_other_decorators_cannot_disappear(self):
        for addition in (b'# outside admitted class\n',b'def outside_guard():\n    return 1\n\n',b'@outside_decorator\n'):
            with self.subTest(addition=addition):
                changed=self.process.replace(b'class Streams:',addition+b'class Streams:',1)
                self.assertNotEqual(self.digest(changed),self.expected)

    def test_decorator_before_admitted_class_stays_outside_erasure(self):
        changed=self.process.replace(b'class OwnedTree:',b'@unapproved_decorator\nclass OwnedTree:',1)
        self.assertNotEqual(self.digest(changed),self.expected)

    def test_duplicate_missing_nonclass_and_malformed_class_bounds_reject(self):
        for changed in (self.process+b'\nclass OwnedTree:\n    pass\n',self.process.replace(b'class OwnedTree:',b'class OtherTree:',1)):
            with self.subTest(changed=changed[-40:]),self.assertRaises(ValueError):
                erase_ancestry_class(changed,'OwnedTree',self.baseline)
        for donor in (b'def OwnedTree():\n    pass\n',self.baseline+b'\ndef outside():\n    pass\n'):
            with self.subTest(donor=donor[-40:]),self.assertRaises(ValueError):
                erase_ancestry_class(self.process,'OwnedTree',donor)
        module=ast.parse(self.process)
        next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='OwnedTree').end_lineno=10**8
        with patch('test_fov_binary_input.ast.parse',return_value=module),self.assertRaisesRegex(ValueError,'bounds'):
            erase_ancestry_class(self.process,'OwnedTree',self.baseline)

    def test_unrelated_test_method_edit_is_visible_after_fake_kernel_reconstruction(self):
        root=Path(__file__).resolve().parents[1];raw=(root/'scripts/test_fov_math_reference.py').read_bytes()
        donor=ancestry_baseline_segments()['fake_kernel']['text'].encode()
        before=erase_ancestry_class(raw,'FakeKernel',donor)
        changed=raw.replace(b'def test_one_isolated_pinned_invocation_and_complete_success(self):',
                            b'def test_one_isolated_pinned_invocation_and_complete_success(self):\n        self.fail("outside scope")',1)
        self.assertNotEqual(erase_ancestry_class(changed,'FakeKernel',donor),before)


if __name__=='__main__':unittest.main()
