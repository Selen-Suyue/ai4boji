import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from ai4boji.catalog import localize
from ai4boji.core import Service, seed_demo
from ai4boji.storage import Store

ROOT = Path(__file__).resolve().parents[1]
DAY = '2026-10-16'  # Friday
PROFILE = {'name': '测试用户', 'age': 25, 'goal': '建立稳定训练习惯', 'minutes': 30,
           'days': [0, 2, 4], 'equipment': 'bodyweight', 'timezone': 'Asia/Shanghai'}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Service(Store(self.tmp.name))
        self.clock = patch.object(Service, 'today', return_value=DAY)
        self.clock.start()
        self.s.save_profile(PROFILE)

    def tearDown(self):
        self.clock.stop()
        self.tmp.cleanup()

    def test_full_workflow_survives_new_service(self):
        self.s.save_checkin({'sleep_hours': 7, 'energy': 4, 'soreness': 1, 'pain': False, 'minutes': 20})
        plan = self.s.generate_plan()
        self.assertEqual(plan['payload']['mode'], 'training')
        self.assertEqual(plan['payload']['minutes'], 20)
        self.assertEqual(len(plan['payload']['exercises']), 3)
        self.s.save_log({'id': 'session-1', 'status': 'completed', 'duration_min': 18,
                        'exercises': [{'exercise_id': 'chair-squat', 'sets': 2, 'reps': 8}]})
        self.s.save_memory({'id': 'memory:weekends', 'text': '周末上午', 'kind': 'preference', 'confirmed': True})
        context = Service(Store(self.tmp.name)).context()
        self.assertEqual(context['profile']['payload']['name'], '测试用户')
        self.assertEqual(context['report']['total_minutes'], 18)
        self.assertEqual(context['report']['training_days'], 1)
        self.assertEqual(len(context['active_memories']), 1)
        self.assertTrue(context['plan']['stale'])
        self.assertIn('completed_today', self.s.generate_plan()['payload']['reason_codes'])

    def test_idempotent_retry_with_original_revision(self):
        data = {'id': 'one', 'status': 'completed', 'duration_min': 20, 'expected_revision': 0}
        first = self.s.save_log(data)
        second = self.s.save_log(data)
        self.assertEqual(first, second)
        self.assertEqual(self.s.report()['total_minutes'], 20)
        self.assertEqual(len(self.s.store.list('log')), 1)

    def test_correction_keeps_history_and_updates_chart(self):
        self.s.save_log({'id': 'one', 'status': 'completed', 'duration_min': 20, 'weight_kg': 60})
        self.s.save_log({'id': 'one', 'status': 'partial', 'duration_min': 10, 'weight_kg': 61, 'expected_revision': 1})
        r = self.s.report()
        self.assertEqual(r['total_minutes'], 10)
        self.assertEqual([p['value'] for p in r['weights']], [61])
        self.assertEqual(self.s.store.history('log:one')[0]['payload']['weight_kg'], 60)
        with self.assertRaises(ValueError):
            self.s.save_log({'id': 'one', 'status': 'completed', 'duration_min': 40, 'expected_revision': 1})

    def test_plan_idempotence_and_input_version(self):
        a = self.s.generate_plan()
        self.assertEqual(a, self.s.generate_plan())
        self.s.save_checkin({'minutes': 15})
        self.assertTrue(self.s.state()['plan']['stale'])
        b = self.s.generate_plan()
        self.assertEqual(b['revision'], 2)
        self.assertNotEqual(a['payload']['fingerprint'], b['payload']['fingerprint'])
        self.assertEqual(b['payload']['exercises'][0]['sets'], 1)
        self.assertEqual(len(self.s.store.history('plan:'+DAY)), 1)

    def test_language_changes_no_prescription(self):
        plan = self.s.generate_plan()
        self.s.save_profile({'locale': 'en'})
        same = self.s.generate_plan()
        self.assertEqual(plan['revision'], same['revision'])
        zh, en = localize(same, 'zh-CN'), localize(same, 'en')
        self.assertNotEqual(zh['payload']['title'], en['payload']['title'])
        self.assertEqual(zh['payload']['minutes'], en['payload']['minutes'])
        self.assertEqual(zh['payload']['fingerprint'], en['payload']['fingerprint'])

    def test_equipment_changes_exercises(self):
        a = self.s.generate_plan()['payload']
        self.s.save_profile({'equipment': 'dumbbells'})
        b = self.s.generate_plan()['payload']
        self.assertNotIn('db-row', [e['exercise_id'] for e in a['exercises']])
        self.assertIn('db-row', [e['exercise_id'] for e in b['exercises']])

    def test_fatigue_and_short_time_switch_to_recovery(self):
        for checkin, reason in [({'sleep_hours': 4}, 'fatigue'), ({'energy': 1}, 'fatigue'),
                               ({'soreness': 4}, 'fatigue'), ({'minutes': 10}, 'short')]:
            with self.subTest(checkin=checkin):
                self.s.save_checkin(checkin)
                plan = self.s.generate_plan()['payload']
                self.assertEqual(plan['mode'], 'recovery')
                self.assertIn(reason, plan['reason_codes'])
                self.assertEqual(plan['exercises'], [])

    def test_previous_day_training_and_off_day(self):
        self.s.save_log({'id': 'yesterday', 'date': '2026-10-15', 'status': 'partial', 'duration_min': 15})
        self.assertIn('yesterday', self.s.generate_plan()['payload']['reason_codes'])
        self.assertIn('off_day', self.s.generate_plan('2026-10-17')['payload']['reason_codes'])

    def test_pain_is_not_lost_after_seven_days(self):
        self.s.save_checkin({'date': '2026-10-01', 'pain': True})
        self.s.save_checkin({'minutes': 30})
        self.assertEqual(self.s.generate_plan()['payload']['mode'], 'hold')
        self.s.save_checkin({'pain': False})
        self.assertEqual(self.s.generate_plan()['payload']['mode'], 'training')

    def test_same_day_pain_log_still_holds(self):
        self.s.save_checkin({'pain': False})
        self.s.save_log({'id': 'pain', 'status': 'partial', 'duration_min': 5, 'pain': True})
        self.assertEqual(self.s.generate_plan()['payload']['mode'], 'hold')

    def test_restriction_holds(self):
        self.s.save_profile({'restrictions': '膝盖持续不适'})
        plan = self.s.generate_plan()['payload']
        self.assertEqual(plan['mode'], 'hold')
        self.assertEqual(plan['minutes'], 0)
        self.assertEqual(plan['exercises'], [])

    def test_missing_is_unknown(self):
        plan = self.s.generate_plan()['payload']
        self.assertIn('missing', plan['reason_codes'])
        self.assertEqual(self.s.report()['unknown_days'], 7)
        saved = self.s.save_log({'id': 'unknown-time', 'status': 'partial'})
        self.assertIsNone(saved['payload']['duration_min'])
        self.assertEqual(self.s.report()['unknown_duration_sessions'], 1)
        self.assertNotIn('weight_kg', saved['payload'])
        self.assertNotIn('pain', saved['payload'])

    def test_expiry_inference_and_permanent_memory_delete(self):
        self.s.save_memory({'id': 'memory:a', 'text': 'test', 'expires': '2026-10-15'})
        self.assertEqual(self.s.context()['active_memories'], [])
        self.s.save_memory({'id': 'memory:a', 'text': 'corrected', 'kind': 'fact', 'confirmed': True})
        self.assertEqual(len(self.s.store.history('memory:a')), 1)
        with self.assertRaises(ValueError):
            self.s.save_memory({'text': 'guess', 'kind': 'inference', 'confirmed': True})
        self.s.store.forget('memory:a')
        self.assertEqual(self.s.store.history('memory:a'), [])
        self.assertEqual(self.s.context()['active_memories'], [])
        self.assertNotIn('corrected', json.dumps(self.s.store.export()))
        with self.assertRaises(ValueError):
            self.s.store.forget('profile')

    def test_validation_rejects_bad_values_without_writing(self):
        for data in [{'age': 17}, {'age': True}, {'minutes': float('nan')}, {'days': [0,0]},
                     {'timezone': 'Mars/Olympus'}, {'unknown': 1}, {'expected_revision': True}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.s.save_profile(data)
        for data in [{'date': '2026-02-30'}, {'date': '2027-01-01'}, {'pain': 'false'}, {'energy': 2.5}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.s.save_checkin(data)
        self.assertEqual(self.s.store.get('profile')['revision'], 1)
        self.assertEqual(self.s.store.list('checkin'), [])

    def test_report_windows_exclude_later_and_older_activity(self):
        for day in ['2026-09-01','2026-10-10','2026-10-16']:
            self.s.save_log({'id': day, 'date': day, 'status': 'completed', 'duration_min': 20})
        r = self.s.report('2026-10-12', 7)
        self.assertEqual(r['training_days'], 1)
        self.assertEqual(r['source_ids'], ['log:2026-10-10'])

    def test_demo_does_not_overwrite_personal_profile(self):
        before = self.s.store.export()
        seed_demo(self.s)
        self.assertEqual(before, self.s.store.export())

    def test_demo_is_idempotent_in_separate_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            demo = Service(Store(directory))
            seed_demo(demo)
            before = demo.store.export()
            seed_demo(demo)
            self.assertEqual(before, demo.store.export())
            self.assertGreater(len(demo.store.list('log')), 5)
            self.assertEqual(self.s.store.list('log'), [])

    def test_timezone_changes_today_not_language(self):
        self.clock.stop()
        fixed = datetime(2026,10,15,17,0,tzinfo=timezone.utc)
        try:
            with patch('ai4boji.core.datetime') as clock:
                clock.now.side_effect = lambda zone: fixed.astimezone(zone)
                self.assertEqual(self.s.today(), '2026-10-16')
                self.s.save_profile({'locale': 'en'})
                self.assertEqual(self.s.today(), '2026-10-16')
                self.s.save_profile({'timezone': 'America/Los_Angeles'})
                self.assertEqual(self.s.today(), '2026-10-15')
        finally:
            self.clock.start()


class CLIIntegrationTests(unittest.TestCase):
    def test_real_subprocess_workflow_and_cross_session_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            def run(command, data=None, lang='zh-CN'):
                proc = subprocess.run([sys.executable,'-m','ai4boji','--data-dir',directory,'--lang',lang]+command,
                    input=json.dumps(data) if data is not None else None, cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                return json.loads(proc.stdout)
            run(['profile'], PROFILE)
            run(['checkin'], {'sleep_hours':7,'minutes':20,'pain':False})
            run(['plan'])
            run(['log'], {'id':'integration-one','status':'completed','duration_min':18})
            run(['log'], {'id':'integration-one','status':'completed','duration_min':18})
            run(['memory'], {'id':'memory:weekend','text':'morning','kind':'preference','confirmed':True})
            ctx=run(['context'],lang='en')
            self.assertEqual(ctx['title'],'AI4薄肌')
            self.assertEqual(ctx['report']['total_minutes'],18)
            self.assertEqual(ctx['active_memories'][0]['payload']['text'],'morning')
            self.assertEqual(len(run(['export'])['entries']),5)

    def test_invalid_json_exits_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            proc=subprocess.run([sys.executable,'-m','ai4boji','--data-dir',directory,'profile'],
                                input='{broken',text=True,capture_output=True,cwd=ROOT)
            self.assertEqual(proc.returncode,2)
            self.assertIn('error',json.loads(proc.stderr))
            self.assertNotIn('Traceback',proc.stderr)


if __name__ == '__main__':
    unittest.main()
