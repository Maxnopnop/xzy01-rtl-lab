import hashlib,json,unittest
from budget_adapter import adapt_request,usage_record,execution_decision

class BudgetTests(unittest.TestCase):
    def test_unknown_not_zero(self):
        x=usage_record(None)
        self.assertTrue(all(v is None for v in x['values'].values()))
        self.assertEqual(len(x['unknown_fields']),5)

    def test_observed_zero_and_nested_reasoning(self):
        x=usage_record({'input_tokens':17,'output_tokens':4,'input_tokens_details':{'cached_tokens':0},'output_tokens_details':{'reasoning_tokens':3}})
        self.assertEqual(x['values']['output_tokens'],4)
        self.assertEqual(x['values']['reasoning_tokens'],3)
        self.assertEqual(x['values']['cached_input_tokens'],0)
        self.assertIsNone(x['values']['total_tokens'])

    def test_chat_completion_and_bad_types(self):
        x=usage_record({'prompt_tokens':5,'completion_tokens':7,'completion_tokens_details':{'reasoning_tokens':-1},'total_tokens':True})
        self.assertEqual(x['values']['input_tokens'],5)
        self.assertEqual(x['values']['output_tokens'],7)
        self.assertIsNone(x['values']['reasoning_tokens'])
        self.assertIsNone(x['values']['total_tokens'])

    def test_only_budget_field_removed(self):
        old={'model':'gpt-5.6-luna','messages':[{'role':'system','content':'a\n'},{'role':'user','content':'原文\n'}],'max_completion_tokens':8192,'stream':False}
        raw=json.dumps(old,ensure_ascii=False).encode('utf-8')
        x=adapt_request(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(x['messages'],old['messages'])
        self.assertEqual(set(old)-set(x),{'max_completion_tokens'})
        with self.assertRaises(ValueError):adapt_request(raw,'0'*64)

    def test_unverified_gates_do_not_enable_dispatch(self):
        x=execution_decision(False,False,False)
        self.assertFalse(x['eligible_for_separate_dispatcher_review'])
        self.assertFalse(x['starts_calls'])
        self.assertFalse(execution_decision(True,True,True)['transport_implemented'])

if __name__=='__main__':unittest.main()
