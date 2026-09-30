import tempfile
import unittest
from pathlib import Path

import batch
import paired_audit as audit
import rtl_lab as lab


class EvidenceTests(unittest.TestCase):
    def test_missing_pair_is_not_functional_failure(self):
        rows=[]
        for pair, statuses in enumerate([('TIMEOUT','TIMEOUT'),('FUNCTION_FAIL','FUNCTION_FAIL'),
                                        ('FUNCTION_FAIL','PASS'),('PASS','FUNCTION_FAIL'),('PASS','PASS')]):
            rows += [dict(pair_id=str(pair),arm=arm,status=status) for arm,status in zip(('control','feedback'),statuses)]
        self.assertEqual(audit.pair_counts(rows),dict(infrastructure_incomplete=1,both_functionally_fail=1,
                                                    feedback_only=1,control_only=1,both_pass=1))

    def test_changed_locked_artifact_rejected_before_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); artifact=root/'response.txt';artifact.write_bytes(b'original')
            batch.atomic(root/'evidence-lock.json',{'response.txt':lab.digest(artifact.read_bytes())})
            artifact.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Evidence changed: response.txt'):
                audit.audit(root)


if __name__=='__main__':unittest.main()
