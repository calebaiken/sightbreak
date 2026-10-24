"""Pure owned-process edge tests; no real child, pidfd or signal is used."""
import unittest
import acquire_fov_math_reference as acquisition
from test_fov_math_reference import FakeKernel


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


if __name__=='__main__':unittest.main()
