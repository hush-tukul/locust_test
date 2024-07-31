import grpc
import vacancy_service_pb2_grpc
import vacancy_service_pb2


def get_vacancies(stub):
    # Create a request for the vacancies
    request = vacancy_service_pb2.GetVacanciesRequest(page=1, limit=100)

    # Call the GetVacancies method on the stub and get the stream
    vacancy_stream = stub.GetVacancies(request)

    # Process the stream of vacancies
    for vacancy in vacancy_stream:
        print(f"Vacancy: {vacancy}")


def run():
    # Establish a channel with the server
    channel = grpc.insecure_channel('vacancies.cyrextech.net:7823')

    # Create a stub (client)
    stub = vacancy_service_pb2_grpc.VacancyServiceStub(channel)

    # Get and print vacancies
    get_vacancies(stub)


if __name__ == '__main__':
    run()
