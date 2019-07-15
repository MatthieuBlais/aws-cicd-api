from chalice import Chalice
from chalicelib.utils.cognito import Cognito
from chalicelib.model.greeting import HelloGreeting
from chalicelib.service import GreetingService

app = Chalice(app_name='greeting-application')

@app.route('/hello', methods=["GET"], cors=True)
def hello():
	email = Cognito.get_email(app)
	queue_number = GreetingService.get_queue_number()
	return HelloGreeting().to_dict(email, queue_number)



