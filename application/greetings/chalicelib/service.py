from random import randint

class GreetingService(object):
	"""docstring for GreetingService"""

	@classmethod
	def get_queue_number(cls):
		return randint(1, 100)