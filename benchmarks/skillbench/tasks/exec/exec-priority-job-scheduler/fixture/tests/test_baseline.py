import unittest
from jobqueue.scheduler import JobScheduler

class SchedulerBaselineTest(unittest.TestCase):
    def test_submit_and_pop(self) -> None:
        sched = JobScheduler()
        sched.submit('job-1')
        popped = sched.pop_ready()
        self.assertIsNotNone(popped)
        self.assertEqual(popped.job_id, 'job-1')
