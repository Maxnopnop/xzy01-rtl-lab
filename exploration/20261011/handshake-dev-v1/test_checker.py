"""Semantic acceptance/rejection witnesses; fixtures are not model outputs."""
import unittest
from checker import check
from fixtures import build

class ContractTests(unittest.TestCase):
    def test_declared_witnesses(self):
        for f in build():
            with self.subTest(name=f['name']):
                result=check(f['rows'],f['episodes'])
                self.assertEqual(result['status'],f['expected_status'],result)
                if f['expected_category']:self.assertIn(f['expected_category'],result['counts'],result)

    def test_legal_latency_and_invalid_bits_preserve_transactions(self):
        fixtures=build();reference=check(fixtures[0]['rows'],fixtures[0]['episodes'])
        for f in fixtures[1:4]:
            result=check(f['rows'],f['episodes'])
            self.assertEqual(result['status'],'PASS',result)
            for left,right in zip(reference['delivered'],result['delivered']):
                self.assertEqual([x['beat'] for x in left],[x['beat'] for x in right])
        self.assertNotEqual(reference['delivered'][0][0]['cycle'],check(fixtures[1]['rows'],fixtures[1]['episodes'])['delivered'][0][0]['cycle'])

    def test_reset_cancel_is_accounted_not_silently_lost(self):
        f=next(x for x in build() if x['name']=='declared_reset_cancels_inflight')
        result=check(f['rows'],f['episodes'])
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['aborted'],[dict(epoch=0,cycle=2,pending=[1,1],unaccepted=1)])

if __name__=='__main__':unittest.main()
