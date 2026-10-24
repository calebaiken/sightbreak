"""UNEXECUTED G3 synthetic wrapper extension; requires approved V4 base.

Only the fixture module may contain this code. It invokes neither real_driver
nor main; solid PNG/OCR/game/OS values remain synthetic format inputs.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil


class DeclaredOriginalLedger(DeclaredProducer):
    """Reuse V4's exact owned-file methods without its scenario/run constructor."""
    def __init__(self,directory):
        self.root=Path(directory)
        self.root.mkdir()  # Fresh sibling; never adopt an existing capture scope.
        self.root_identity=self.directory_identity(self.root.lstat())
        self.owned={};self.opened=[];self.directories={}


class WrapperDeclaredProducer(DeclaredProducer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.originals=DeclaredOriginalLedger(self.root.with_name(self.root.name+'.controller-capture'))
    def put(self,name,raw):
        if name in ('controller-stdout.log','controller-stderr.log'):
            self.originals.put(name,raw)
        else:super().put(name,raw)
    def run(self):
        invocation_error=None;publication_errors=[];result=None
        # Scope creation is before this protected invocation, as in real_driver.
        try:
            # Original streams exist before the synthetic main's first metadata.
            self.originals.put('controller-stdout.log',b'')
            self.originals.put('controller-stderr.log',b'')
            result=super().run()
        except BaseException as error:invocation_error=error
        finally:
            close_errors=self.originals.close_owned()
            if close_errors:
                close_error=RuntimeError('Synthetic original stream close failed: '+str(close_errors))
                if invocation_error is not None:close_error.__cause__=invocation_error
                invocation_error=close_error
            # Model the frozen wrapper's two independent exclusive binary copies.
            for name in ('controller-stdout.log','controller-stderr.log'):
                source=self.originals.root/name;target=self.root/name
                try:
                    self.verify_namespace();self.originals.verify_namespace()
                    with source.open('rb') as reader,target.open('xb') as writer:
                        shutil.copyfileobj(reader,writer)
                    self.verify_namespace();self.originals.verify_namespace()
                except BaseException as error:
                    publication_errors.append(dict(path=str(target),error=type(error).__name__+': '+str(error)))
            try:
                self.verify_namespace();self.originals.verify_namespace()
                publication=dict(invocation_error=None if invocation_error is None else
                    type(invocation_error).__name__+': '+str(invocation_error),
                    publication_errors=copy.deepcopy(publication_errors),
                    capture_scope='Complete original streams retained; publication never overwrites',
                    files=[dict(path=name,bytes=(self.originals.root/name).stat().st_size,
                                sha256=hashlib.sha256((self.originals.root/name).read_bytes()).hexdigest())
                           for name in ('controller-stdout.log','controller-stderr.log')
                           if (self.originals.root/name).is_file()])
                with (self.originals.root/'publication.json').open('x',encoding='utf-8') as receipt:
                    receipt.write(json.dumps(publication,indent=2,allow_nan=False)+'\n')
                self.verify_namespace();self.originals.verify_namespace()
            except BaseException as error:
                publication_errors.append(dict(path=str(self.originals.root/'publication.json'),
                                               error=type(error).__name__+': '+str(error)))
        if publication_errors:
            raise RuntimeError('Controller stream publication failed; originals and partial files retained: '+str(publication_errors)) from invocation_error
        if invocation_error is not None:raise invocation_error
        return result
