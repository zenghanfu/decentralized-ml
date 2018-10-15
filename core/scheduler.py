import logging
import time
import json
from collections import deque
from threading import Event, Timer
from multiprocessing import Pool

from core.utils.dmljob import DMLJob
from core.runner import DMLRunner
from core.configuration import ConfigurationManager


logging.basicConfig(level=logging.DEBUG,
					format='[Scheduler] %(asctime)s %(levelname)s %(message)s')

class DMLScheduler(object):
	"""
	DML Scheduler

	This class schedules and manages the execution of DMLJobs using the
	DMLRunner.

	NOTE: Supports a multithreaded environment using multiprocessing.
	NOTE2: Only supports one dataset type.

	"""

	def __init__(self, config_manager):
		"""
		Initializes the instance.
		"""
		logging.info("Setting up scheduler...")
		self.queue = deque()
		self.event = Event()
		self.processed = []
		self.history = []

		config = config_manager.get_config()
		self.dataset_path = config.get("GENERAL", "dataset_path")
		self.frequency_in_mins = config.getint("SCHEDULER", "frequency_in_mins")
		self.num_runners = config.getint("SCHEDULER", "num_runners")
		self.max_tries = config.getint("SCHEDULER", "max_tries")

		self.pool = Pool(processes=self.num_runners)
		self.runners = [DMLRunner(config_manager) for _ in range(self.num_runners)]
		self.current_jobs = [None for _ in range(self.num_runners)]
		self.current_results = [None for _ in range(self.num_runners)]
		logging.info("Scheduler is set up!")

	def add_job(self, dml_job):
		"""
		Add a job to the queue.
		"""
		assert type(dml_job) is DMLJob, "Job is not of type DMLJob."
		logging.info("Scheduling job...")
		self.queue.append(dml_job)

	def start_cron(self, period_in_mins=None):
		"""
		CRON job to run next jobs on runners, if applicable. Runs asynchronously.
		"""
		if not period_in_mins:
			period_in_mins = self.frequency_in_mins
		logging.info("Starting cron...")
		self._runners_run_next_jobs_as_event(period_in_mins)
		logging.info("Cron started!")

	def stop_cron(self):
		"""
		Tell the scheduler to stop scheduling jobs.
		"""
		logging.info("Stopping cron...")
		self.event.set()
		logging.info("Cron stopped!")

	def reset(self, reset_history=False):
		"""
		Resets the scheduler.
		"""
		logging.info("Resetting scheduler...")
		self.queue = deque()
		self.processed = []
		if reset_history:
			self.history = []
		self.event = Event()
		logging.info("Scheduler reset!")

	def runners_run_next_jobs(self):
		"""
		Check each job to see if it has a job running. If not, have the runner
		run the next job on the queue asynchronously of the others and collect
		the result of the job that was running before (if applicable).

		If job that runner is running fails, then put the job back in queue.
		If job failed more than num_tries times, don't put the job back in
		thw queue.
		"""
		for i, runner in enumerate(self.runners):
			# Check if there's any finished jobs and process them.
			if self.current_results[i]:
				#If the job results are available
				finished_results = self.current_results[i].get()
				if finished_results.status == 'successful':
					# If the job finished successfully...
					self.processed.append(finished_results)
					self.history.append(finished_results)
					self.current_jobs[i] = None
					self.current_results[i] = None
				elif finished_results.status == 'failed':
					# If some error occurred
					job_to_run = self.current_jobs[i]
					job_to_run.num_tries_left -= 1
					if job_to_run.num_tries_left > 0:
						# Still has tries remaining, so put back in queue
						self.add_job(job_to_run)
					else:
						# Log error, ignore failed job
						logging.error(finished_results.error_message)
						self.current_jobs[i] = None
						self.current_results[i] = None

			# Check if there's any queued jobs and schedule them.
			if self.queue:
				# If there's something to be scheduled...
				job_to_run = self.queue.popleft()
				job_to_run.num_tries_left = self.max_tries
				# self.current_jobs[i] = runner.run_job(job_to_run)
				self.current_jobs[i] = job_to_run
				self.current_results[i] = self.pool.apply_async(
					runner.run_job,
					(job_to_run,)
				)

	def _runners_run_next_jobs_as_event(self, period_in_mins):
		"""
		Trigger above method every period.
		"""
		logging.info("Running cron job...")
		self.runners_run_next_jobs()
		if not self.event.is_set():
			Timer(
				period_in_mins * 60,
				self._runners_run_next_jobs_as_event,
				[period_in_mins]
			).start()
