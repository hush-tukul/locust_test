


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

    @task
    def create_vacancy_recurring(self):
        # Ensure user is authenticated
        if not self.authenticated_user:
            self.authenticate_user()

        if self.authenticated_user:
            # Create vacancy with pseudo-random data
            self.create_vacancy()

        # Sleep for 10 seconds before the next task
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
            events.request.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=(time.time() - start_time) * 1000,
                exception=e
            )

if __name__ == '__main__':
    import locust.main
    locust.main.main()



































"""ALMOST READY CODE"""
# from locust import User, task, between
# import grpc
# import auth_service_pb2
# import auth_service_pb2_grpc
# import rpc_signin_user_pb2
# import rpc_signin_user_pb2_grpc
# import rpc_create_vacancy_pb2
# import rpc_update_vacancy_pb2
# import vacancy_service_pb2_grpc
# import vacancy_service_pb2
# import random
# import string
# import time
#
# # Dictionary of user credentials
# bloom_users = {
#     'thrtjtrgrt@belgianairways.com': 'password',
#     'egregerve@belgianairways.com': 'password',
#     'jtjuhtjut@belgianairways.com': 'password',
# }
#
# class UserBehavior(User):
#     wait_time = between(5, 15)
#     host = "vacancies.cyrextech.net:7823"  # Note: no 'http://' prefix for gRPC
#
#     def on_start(self):
#         # Create channels and stubs for authentication and vacancy services
#         self.channel = grpc.insecure_channel(self.host)
#         self.auth_stub = auth_service_pb2_grpc.AuthServiceStub(self.channel)
#         self.vacancy_stub = vacancy_service_pb2_grpc.VacancyServiceStub(self.channel)
#         self.authenticated_user = None
#
#         # Authenticate user
#         self.authenticate_user()
#
#     def authenticate_user(self):
#         # Select a random user
#         email, password = random.choice(list(bloom_users.items()))
#
#         # Define the sign-in request payload
#         signin_request = rpc_signin_user_pb2.SignInUserInput(
#             email=email,
#             password=password
#         )
#
#         try:
#             # Send the gRPC sign-in request and get the response
#             response = self.auth_stub.SignInUser(signin_request)
#             print(f"Logged in as {email}: {response}")
#
#             # Assuming successful sign-in, store the authenticated user
#             self.authenticated_user = email
#
#         except grpc.RpcError as e:
#             print(f"gRPC failed with status code {e.code()}: {e.details()}")
#             self.authenticated_user = None
#
#     @task
#     def create_vacancy_recurring(self):
#         # Ensure user is authenticated
#         if not self.authenticated_user:
#             self.authenticate_user()
#
#         if self.authenticated_user:
#             # Create vacancy with pseudo-random data
#             self.create_vacancy()
#
#         # Sleep for 30 seconds before the next task
#         time.sleep(10)
#
#     # @task
#     # def fetch_vacancies_periodically(self):
#     #     # Ensure user is authenticated
#     #     if not self.authenticated_user:
#     #         self.authenticate_user()
#     #
#     #     if self.authenticated_user:
#     #         self.get_vacancies()
#     #
#     #     # Sleep for 45 seconds before fetching the list again
#     #     time.sleep(5)
#
#     def create_vacancy(self):
#         # Generate pseudo-random data for vacancy details
#         title = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
#         description = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
#         division = random.randint(0, 3)
#         country = random.choice(['USA', 'Canada', 'UK', 'Germany', 'France'])
#
#         # Define the create vacancy request payload
#         vacancy_request = rpc_create_vacancy_pb2.CreateVacancyRequest(
#             Title=title,
#             Description=description,
#             Division=division,
#             Country=country
#         )
#
#         try:
#             # Send the gRPC create vacancy request and get the response
#             response = self.vacancy_stub.CreateVacancy(vacancy_request)
#             print(f"Vacancy created: {response}")
#
#             # Store the created vacancy ID
#             vacancy_id = response.vacancy.Id
#
#             # Update the created vacancy
#             self.update_vacancy(vacancy_id)
#
#         except grpc.RpcError as e:
#             if e.code() == grpc.StatusCode.ALREADY_EXISTS:
#                 print(f"Vacancy with title '{title}' already exists. Skipping creation.")
#             else:
#                 print(f"gRPC failed with status code {e.code()}: {e.details()}")
#
#     def update_vacancy(self, vacancy_id):
#         # Generate new pseudo-random data for updating the vacancy
#         new_description = ''.join(random.choices(string.ascii_uppercase + string.digits, k=25))
#
#         # Define the update vacancy request payload
#         update_request = rpc_update_vacancy_pb2.UpdateVacancyRequest(
#             Id=vacancy_id,
#             Description=new_description
#         )
#
#         try:
#             # Send the gRPC update vacancy request and get the response
#             response = self.vacancy_stub.UpdateVacancy(update_request)
#             print(f"Vacancy updated: {response}")
#
#             # Fetch the updated vacancy
#             self.get_vacancy(vacancy_id)
#
#         except grpc.RpcError as e:
#             print(f"gRPC failed with status code {e.code()}: {e.details()}")
#
#     def get_vacancy(self, vacancy_id):
#         # Define the get vacancy request payload
#         get_vacancy_request = vacancy_service_pb2.VacancyRequest(
#             Id=vacancy_id
#         )
#
#         try:
#             # Send the gRPC get vacancy request and get the response
#             response = self.vacancy_stub.GetVacancy(get_vacancy_request)
#             print(f"Fetched vacancy details: {response}")
#
#             # Delete the fetched vacancy
#             self.delete_vacancy(vacancy_id)
#
#         except grpc.RpcError as e:
#             print(f"gRPC failed with status code {e.code()}: {e.details()}")
#
#     def get_vacancies(self):
#         # Define the get vacancies request payload with pagination
#         get_vacancies_request = vacancy_service_pb2.GetVacanciesRequest(
#             page=20,  # Example: request the first page
#             limit=20  # Example: request up to 10 vacancies per page
#         )
#
#         try:
#             # Send the gRPC get vacancies request and handle the streaming responses
#             print("Fetching list of vacancies:")
#             for response in self.vacancy_stub.GetVacancies(get_vacancies_request):
#                 print(f"Vacancy: {response}")
#
#         except grpc.RpcError as e:
#             print(f"gRPC failed with status code {e.code()}: {e.details()}")
#
#     def delete_vacancy(self, vacancy_id):
#         # Define the delete vacancy request payload
#         delete_request = vacancy_service_pb2.VacancyRequest(
#             Id=vacancy_id
#         )
#
#         try:
#             # Send the gRPC delete vacancy request and get the response
#             response = self.vacancy_stub.DeleteVacancy(delete_request)
#             print(f"Vacancy deleted: {response}")
#
#         except grpc.RpcError as e:
#             print(f"gRPC failed with status code {e.code()}: {e.details()}")
#
# if __name__ == '__main__':
#     import locust.main
#     locust.main.main()















"""WORKING CODE!!!!!!!!!"""
# from locust import User, task, between
# import grpc
# import auth_service_pb2
# import auth_service_pb2_grpc
# import rpc_signin_user_pb2
# import rpc_signin_user_pb2_grpc
# import random
#
# # Dictionary of user credentials
# bloom_users = {
#     'thrtjtrgrt@belgianairways.com': 'password',
#     'egregerve@belgianairways.com': 'password',
#     'jtjuhtjut@belgianairways.com': 'password',
# }
#
# class UserBehavior(User):
#     wait_time = between(5, 15)
#     host = "vacancies.cyrextech.net:7823"  # Note: no 'http://' prefix for gRPC
#
#     def on_start(self):
#         # Create a channel and stub
#         self.channel = grpc.insecure_channel(self.host)
#         self.stub = auth_service_pb2_grpc.AuthServiceStub(self.channel)
#
#     @task
#     def sign_in(self):
#         # Select a random user
#         email, password = random.choice(list(bloom_users.items()))
#
#         # Define the request payload
#         signin_request = rpc_signin_user_pb2.SignInUserInput(
#             email=email,
#             password=password
#         )
#
#         try:
#             # Send the gRPC request and get the response
#             response = self.stub.SignInUser(signin_request)
#             print(f"Logged in as {email}: {response}")
#         except grpc.RpcError as e:
#             print(f"gRPC failed with status code {e.code()}: {e.details()}")
#
# if __name__ == '__main__':
#     import locust.main
#     locust.main.main()
