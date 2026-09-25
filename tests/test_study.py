import copy
import json
import os
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from fan_agent.study import StudyService, AIError, assess, FIELDS
from fan_agent.server import make_server


def complete():
    return dict(diameter_mm=1200, room_x_m=4, room_y_m=4, room_z_m=3,
                rotor_height_m=2.5, sampling_height_m=1.2, direction='cw', rpms=[250,300], unsupported=[])

class ProposalTests(unittest.TestCase):
    def test_comparison_and_gate(self):
        p=assess(complete())
        self.assertEqual([c['rpm'] for c in p['cases']], [250,300])
        self.assertEqual(p['status'], 'proposal_ready')
        self.assertFalse(p['can_run']); self.assertIsNone(p['results'])
        self.assertNotIn('geometry_id', p['cases'][0])

    def test_missing_is_not_invented(self):
        d={k:None for k in FIELDS};d.update(direction=None,rpms=[250,300],unsupported=[])
        p=assess(d)
        self.assertEqual(p['status'],'needs_inputs'); self.assertEqual(p['cases'],[])
        self.assertIn('room_x_m',p['missing_inputs'])

    def test_partial_cross_field_errors(self):
        d=complete();d['direction']=None;d['rotor_height_m']=4
        self.assertEqual(assess(d)['status'],'invalid')

    def test_rejects_bad_output(self):
        for field,value in [('rpms',[float('nan')]),('rpms',[True]),('rpms',[1,2,3,4,5]),('rpms',[250,250]),('room_x_m',False),('direction',[])]:
            with self.subTest(field=field,value=value):
                d=complete();d[field]=value
                with self.assertRaises(ValueError):assess(d)
        d=complete();d['can_run']=True
        with self.assertRaises(ValueError):assess(d)

    def test_out_of_range_and_unsupported(self):
        d=complete();d['rpms']=[4000]
        self.assertEqual(assess(d)['status'],'invalid')
        d=complete();d['unsupported']=['Change blade pitch']
        self.assertEqual(assess(d)['cases'],[])

    def test_prompt_contract(self):
        service=StudyService()
        for raw in ([],{}, {'prompt':''},{'prompt':'a'*4001},{'prompt':'x','geometry':'secret'}):
            with self.assertRaises(ValueError):service.propose(raw)

    @patch.dict(os.environ,{},clear=True)
    def test_configuration(self):
        self.assertFalse(StudyService().status()['configured'])
        self.assertEqual(StudyService().status()['provider'],'openai')
        with patch.dict(os.environ,{'OPENAI_API_KEY':'k','FAN_AGENT_AI_MODEL':'m'}):
            self.assertTrue(StudyService().status()['configured'])
        with self.assertRaises(AIError):StudyService().propose({'prompt':'Compare 250 and 300 RPM'})

    @patch.dict(os.environ,{'FAN_AGENT_AI_PROVIDER':'openai','OPENAI_API_KEY':'test-secret','FAN_AGENT_AI_MODEL':'test-model'},clear=True)
    def test_real_transport_contract_with_mock_response(self):
        from unittest.mock import MagicMock
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(complete())}]}]}
        context=MagicMock();context.__enter__.return_value.read.return_value=json.dumps(response).encode()
        with patch('fan_agent.study.urlopen',return_value=context) as call:
            result=StudyService().propose({'prompt':'Compare this ceiling fan at 250 and 300 RPM'})
        request=call.call_args.args[0];payload=json.loads(request.data)
        self.assertFalse(payload['store']);self.assertNotIn('tools',payload)
        self.assertTrue(payload['text']['format']['strict'])
        self.assertEqual(call.call_args.kwargs['timeout'],45)
        self.assertFalse(result['can_run'])
        self.assertNotIn('test-secret',json.dumps(result))

    @patch.dict(os.environ,{'FAN_AGENT_AI_PROVIDER':'openai','OPENAI_API_KEY':'test-secret','FAN_AGENT_AI_MODEL':'test-model'},clear=True)
    def test_timeout_no_retry(self):
        with patch('fan_agent.study.urlopen',side_effect=TimeoutError) as call:
            with self.assertRaises(AIError):StudyService().propose({'prompt':'Compare fan'})
        self.assertEqual(call.call_count,1)

    @patch.dict(os.environ,{'FAN_AGENT_AI_PROVIDER':'openai','OPENAI_API_KEY':'test-secret','FAN_AGENT_AI_MODEL':'test-model'},clear=True)
    def test_refusal_incomplete_and_invalid_json(self):
        from unittest.mock import MagicMock
        for response in ({'status':'incomplete'}, {'status':'completed','output':[{'type':'message','content':[{'type':'refusal'}]}]}, {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'no json'}]}]}):
            context=MagicMock();context.__enter__.return_value.read.return_value=json.dumps(response).encode()
            with patch('fan_agent.study.urlopen',return_value=context):
                with self.assertRaises(AIError):StudyService().propose({'prompt':'Fan study'})

    def test_http_flow_does_not_create_cases(self):
        with tempfile.TemporaryDirectory() as root:
            server=make_server(0,root);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
            base='http://127.0.0.1:'+str(server.server_address[1])
            try:
                with patch.object(StudyService,'extract',return_value=complete()):
                    req=Request(base+'/api/studies/propose',data=json.dumps({'prompt':'Compare fan'}).encode(),headers={'Content-Type':'application/json'})
                    result=json.load(urlopen(req))
                    self.assertEqual(len(result['cases']),2)
                    self.assertEqual(json.load(urlopen(base+'/api/cases')),[])
                    req=Request(base+'/api/studies/propose',data=b'{"prompt":"x"}',headers={'Content-Type':'application/json','Origin':'https://other.example'})
                    with self.assertRaises(HTTPError) as err:urlopen(req)
                    self.assertEqual(err.exception.code,403)
            finally:server.shutdown();server.server_close();t.join()


@patch.dict(os.environ, {'FAN_AGENT_AI_PROVIDER':'gemini','GEMINI_API_KEY':'gemini-secret','FAN_AGENT_AI_MODEL':'gemini-test'}, clear=True)
class GeminiTests(unittest.TestCase):
    def response(self, obj):
        from unittest.mock import MagicMock
        context=MagicMock();context.__enter__.return_value.read.return_value=json.dumps(obj).encode()
        return context

    def test_transport_and_gate(self):
        obj={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'private reasoning','thought':True},{'text':json.dumps(complete())}]}}]}
        with patch('fan_agent.study.urlopen',return_value=self.response(obj)) as call:
            result=StudyService().propose({'prompt':'Compare ceiling fan RPM'})
        req=call.call_args.args[0];body=json.loads(req.data)
        self.assertIn('generativelanguage.googleapis.com',req.full_url)
        self.assertNotIn('gemini-secret',req.full_url)
        self.assertEqual(req.get_header('X-goog-api-key'),'gemini-secret')
        self.assertEqual(body['generationConfig']['responseMimeType'],'application/json')
        self.assertNotIn('tools',body);self.assertFalse(result['can_run'])
        self.assertEqual(len(result['cases']),2)

    def test_blocked_truncated_empty_and_malformed(self):
        for obj in ({'promptFeedback':{'blockReason':'SAFETY'}},{'candidates':[]},{'candidates':[{'finishReason':'MAX_TOKENS'}]}, {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'bad json'}]}}]}):
            with patch('fan_agent.study.urlopen',return_value=self.response(obj)):
                with self.assertRaises(AIError): StudyService().propose({'prompt':'Fan'})

    def test_no_fallback_to_other_provider(self):
        with patch.dict(os.environ,{'GEMINI_API_KEY':'','OPENAI_API_KEY':'other'}):
            self.assertFalse(StudyService().status()['configured'])
        with patch.dict(os.environ,{'FAN_AGENT_AI_MODEL':'../bad?key=x'}):
            self.assertFalse(StudyService().status()['configured'])
