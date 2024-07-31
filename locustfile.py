
from datetime import datetime

import gevent
from locust import User, task, between, events
import grpc
import auth_service_pb2
import auth_service_pb2_grpc
import rpc_signin_user_pb2
import rpc_signin_user_pb2_grpc
import rpc_create_vacancy_pb2
import rpc_update_vacancy_pb2
import vacancy_service_pb2_grpc
import vacancy_service_pb2
import random
import string
import time

# Dictionary of user credentials
bloom_users = {
    'thrtjtrgrt@belgianairways.com': 'password',
    'egregerve@belgianairways.com': 'password',
    'jtjuhtjut@belgianairways.com': 'password',
}


class UserBehavior(User):
    wait_time = between(5, 15)
    host = "vacancies.cyrextech.net:7823"  # Note: no 'http://' prefix for gRPC




    def on_start(self):
        # Create channels and stubs for authentication and vacancy services
        self.channel = grpc.insecure_channel(self.host)
        self.auth_stub = auth_service_pb2_grpc.AuthServiceStub(self.channel)
        self.vacancy_stub = vacancy_service_pb2_grpc.VacancyServiceStub(self.channel)
        self.authenticated_user = None

        # Authenticate user
        self.authenticate_user()
        # Start the background task
        self.start_background_function()





    def authenticate_user(self):
        # Select a random user
        email, password = random.choice(list(bloom_users.items()))

        # Define the sign-in request payload
        signin_request = rpc_signin_user_pb2.SignInUserInput(
            email=email,
            password=password
        )

        start_time = time.time()
        try:
            # Send the gRPC sign-in request and get the response
            response = self.auth_stub.SignInUser(signin_request)
            print(f"Logged in as {email}: {response}")

            # Assuming successful sign-in, store the authenticated user
            self.authenticated_user = email

            # Trigger Locust success event
            events.request.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=(time.time() - start_time) * 1000,  # Convert to milliseconds
                response_length=len(str(response))  # Assuming the response is a string; adjust as necessary
            )

        except grpc.RpcError as e:
            print(f"gRPC failed with status code {e.code()}: {e.details()}")
            self.authenticated_user = None

            # Trigger Locust failure event
            events.user_error.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=(time.time() - start_time) * 1000,
                exception=e
            )

    def start_background_function(self):
        """ Start a background function that prints its name every 5 seconds """
        self.background_greenlet = gevent.spawn(self.background_function)

    def background_function(self):
        """ Background function that runs every 5 seconds """
        while True:
            start_time = datetime.now()
            print(f"Background function running...{start_time.strftime('%H:%M:%S')}")
            request = vacancy_service_pb2.GetVacanciesRequest(page=1, limit=5)
            print(f"request: {request} type: {type(request)}")
            #
            # vacancy_stream = self.vacancy_stub.GetVacancies(request)
            # try:
            #     # Process the stream of vacancies
            #     for vacancy in vacancy_stream:
            #         print(f"Vacancy: {vacancy}")
            #
            # except Exception as e:
            #     print(f"{e}")

            gevent.sleep(5)  # Sleep for 5 seconds






    @task
    def create_vacancy_recurring(self):
        # Ensure user is authenticated
        if not self.authenticated_user:
            self.authenticate_user()

        if self.authenticated_user:
            start_time = time.time()
            print(f"create_vacancy_recurring start_time: {start_time}")

            # Create vacancy with pseudo-random data
            self.create_vacancy()
            time.sleep(10)

    def create_vacancy(self):
        # Generate pseudo-random data for vacancy details
        title = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        description = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        division = random.randint(0, 3)
        country = random.choice(['USA', 'Canada', 'UK', 'Germany', 'France'])

        # Define the create vacancy request payload
        vacancy_request = rpc_create_vacancy_pb2.CreateVacancyRequest(
            Title=title,
            Description=description,
            Division=division,
            Country=country
        )

        start_time = time.time()
        try:
            # Send the gRPC create vacancy request and get the response
            response = self.vacancy_stub.CreateVacancy(vacancy_request)
            print(f"Vacancy created: {response}")

            # Store the created vacancy ID
            vacancy_id = response.vacancy.Id

            # Update the created vacancy
            self.update_vacancy(vacancy_id)

            # Trigger Locust success event
            events.request.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(str(response))
            )

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                print(f"Vacancy with title '{title}' already exists. Skipping creation.")
            else:
                print(f"gRPC failed with status code {e.code()}: {e.details()}")

            # Trigger Locust failure event
            events.request_failure.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=(time.time() - start_time) * 1000,
                exception=e
            )

    def update_vacancy(self, vacancy_id):
        # Generate new pseudo-random data for updating the vacancy
        new_description = ''.join(random.choices(string.ascii_uppercase + string.digits, k=25))

        # Define the update vacancy request payload
        update_request = rpc_update_vacancy_pb2.UpdateVacancyRequest(
            Id=vacancy_id,
            Description=new_description
        )

        start_time = time.time()
        try:
            # Send the gRPC update vacancy request and get the response
            response = self.vacancy_stub.UpdateVacancy(update_request)
            print(f"Vacancy updated: {response}")

            # Fetch the updated vacancy
            self.get_vacancy(vacancy_id)

            # Trigger Locust success event
            events.request.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(str(response))
            )

        except grpc.RpcError as e:
            print(f"gRPC failed with status code {e.code()}: {e.details()}")

            # Trigger Locust failure event
            events.request_failure.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=(time.time() - start_time) * 1000,
                exception=e
            )

    def get_vacancy(self, vacancy_id):
        # Define the get vacancy request payload
        get_vacancy_request = vacancy_service_pb2.VacancyRequest(
            Id=vacancy_id
        )

        start_time = time.time()
        try:
            # Send the gRPC get vacancy request and get the response
            response = self.vacancy_stub.GetVacancy(get_vacancy_request)
            print(f"Fetched vacancy details: {response}")

            # Delete the fetched vacancy
            self.delete_vacancy(vacancy_id)

            # Trigger Locust success event
            events.request.fire(
                request_type="gRPC",
                name="GetVacancy",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(str(response))
            )

        except grpc.RpcError as e:
            print(f"gRPC failed with status code {e.code()}: {e.details()}")

            # Trigger Locust failure event
            events.request_failure.fire(
                request_type="gRPC",
                name="GetVacancy",
                response_time=(time.time() - start_time) * 1000,
                exception=e
            )

    def delete_vacancy(self, vacancy_id):
        # Define the delete vacancy request payload
        delete_request = vacancy_service_pb2.VacancyRequest(
            Id=vacancy_id
        )

        start_time = time.time()
        try:
            # Send the gRPC delete vacancy request and get the response
            response = self.vacancy_stub.DeleteVacancy(delete_request)
            print(f"Vacancy deleted: {response}")

            # Trigger Locust success event
            events.request.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=(time.time() - start_time) * 1000,
                response_length=len(str(response))
            )

        except grpc.RpcError as e:
            print(f"gRPC failed with status code {e.code()}: {e.details()}")

            # Trigger Locust failure event
            events.request_failure.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=(time.time() - start_time) * 1000,
                exception=e
            )







