from chalicelib.config import APPLICATION

class HelloGreeting(object):
	"""docstring for HelloGreeting"""

	@classmethod
	def to_dict(cls, email, queue_number):
		return {
			"type": "hello",
			"message": "Hello {}! Welcome to {}! Your queue number is {}.".format(email, APPLICATION, queue_number)
		}
		