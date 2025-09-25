import io
import json
import pytest
from squirrel_server import SquirrelServerHandler
from squirrel_db import SquirrelDB

# use @todo to cause pytest to skip that section
# handy for stubbing things out and then coming back later to finish them.
# @todo is heirarchical, and not sequential. Meaning that
# it will not skip 'peers' of other todos, only children.
todo = pytest.mark.skip(reason='TODO: pending spec')

class FakeRequest():
    def __init__(self, mock_wfile, method, path, body=None):
        self._mock_wfile = mock_wfile
        self._method = method
        self._path = path
        self._body = body

    def sendall(self, x):
        return

    #this is not a 'makefile' like in c++ instead it 'makes' a response file
    def makefile(self, *args, **kwargs):
        if args[0] == 'rb':
            if self._body:
                headers = 'Content-Length: {}\r\n'.format(len(self._body))
                body = self._body
            else:
                headers = ''
                body = ''
            request = bytes('{} {} HTTP/1.0\r\n{}\r\n{}'.format(self._method, self._path, headers, body), 'utf-8')
            return io.BytesIO(request)
        elif args[0] == 'wb':
            return self._mock_wfile

#dummy client and dummy server to pass as params
#when creating SquirrelServerHandler
@pytest.fixture
def dummy_client():
    return ('127.0.0.1', 80)

@pytest.fixture
def dummy_server():
    return None

#a patch for mocking the DB initialize 
# function - this gets called a lot.
@pytest.fixture
def mock_db_init(mocker):
    return mocker.patch.object(SquirrelDB, '__init__', return_value=None)


@pytest.fixture
def mock_db_create_squirrel(mocker):
    return mocker.patch.object(SquirrelDB, 'createSquirrel')

@pytest.fixture
def mock_db_update_squirrel(mocker):
    return mocker.patch.object(SquirrelDB, 'updateSquirrel')

@pytest.fixture
def mock_db_delete_squirrel(mocker):
    return mocker.patch.object(SquirrelDB, 'deleteSquirrel')

@pytest.fixture
def mock_db_get_squirrels(mocker, mock_db_init):
    return mocker.patch.object(SquirrelDB, 'getSquirrels', return_value=['squirrel'])

@pytest.fixture
def mock_db_get_squirrel(mocker, mock_db_init):
    return mocker.patch.object(SquirrelDB, 'getSquirrel', return_value={'id':1, 'name': 'Squeaky','size':'medium'})

@pytest.fixture
def mock_db_get_squirrel_not_found(mocker):
    return mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)

# patch SquirrelServerHandler to make our FakeRequest work correctly
@pytest.fixture(autouse=True)
def patch_wbufsize(mocker):
    mocker.patch.object(SquirrelServerHandler, 'wbufsize', 1)
    mocker.patch.object(SquirrelServerHandler, 'end_headers')


# Fake Requests
@pytest.fixture
def fake_get_squirrels_request(mocker):
    return FakeRequest(mocker.Mock(), 'GET', '/squirrels')

@pytest.fixture
def fake_get_one_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(),'GET', '/squirrels/1')

@pytest.fixture
def fake_update_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(), 'PUT', '/squirrels/1', body='Squeaky&size=large')

@pytest.fixture
def fake_delete_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(),'DELETE', '/squirrels/1')

@pytest.fixture
def fake_create_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(), 'POST', '/squirrels', body='name=Chippy&size=small')

@pytest.fixture
def fake_bad_request(mocker):
    return FakeRequest(mocker.Mock(), 'POST', '/squirrels', body='name=Josh&')

@pytest.fixture
def fake_not_found_request(mocker):
    return FakeRequest(mocker.Mock(), 'GET', '/nonexistent')

#send_response, send_header and end_headers are inherited functions
#from the BaseHTTPRequestHandler. Go look at documentation here:
# https://docs.python.org/3/library/http.server.html
# Seriously. Go look at it. Pay close attention to what wfile is. :o)
# this fixture mocks all of the send____ that we use. 
# It is really just for convenience and cleanliness of code.
@pytest.fixture
def mock_response_methods(mocker):
    mock_send_response = mocker.patch.object(SquirrelServerHandler, 'send_response')
    mock_send_header = mocker.patch.object(SquirrelServerHandler, 'send_header')
    mock_end_headers = mocker.patch.object(SquirrelServerHandler, 'end_headers')
    return mock_send_response, mock_send_header, mock_end_headers


#tests begin here. Your tests should look wildly different. 
# you should begin testing where it makes sense to you.
def describe_SquirrelServerHandler():

    def describe_retrieve_squirrels_functionality():

        def it_queries_db_for_squirrels(mocker, dummy_client, dummy_server):
            #setup
            mock_get_squirrels = mocker.patch.object(SquirrelDB, 'getSquirrels', return_value=['squirrel'])
            fake_get_squirrels_request = FakeRequest(mocker.Mock(), 'GET', '/squirrels')
            
            #do the thing
            SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)

            #assert that the thing was done
            mock_get_squirrels.assert_called_once()

        def it_returns_200_status_code(fake_get_squirrels_request, dummy_client, dummy_server, mock_response_methods):
            
            #set up
            # note: this line 'expands' mock_response_methods into its respective parts
            # only mock_send_response is used in this test. 
            mock_send_response, mock_send_header, mock_end_headers = mock_response_methods
                 
            # do the thing.
            SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
            
            # assert methods calls and arguments
            mock_send_response.assert_called_once_with(200)

        #look at these examples. They use fixtures. What fixtures should you use?
        def it_sends_json_content_type_header(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels, mock_response_methods):
            mock_send_response, mock_send_header, mock_end_headers = mock_response_methods
            SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
            mock_send_header.assert_called_once_with("Content-Type", "application/json")

        def it_calls_end_headers(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels, mock_response_methods):
            mock_send_response, mock_send_header, mock_end_headers = mock_response_methods
            SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
            mock_end_headers.assert_called_once()


        # Note that we're doing something with the response from the
        # SquirrelServerHandler in this test. 
        # wfile is the object used to write back the HTTP response from the server.
        # here, we're asserting that it is getting called and being passed the json 
        # response that we mocked in the mock_db_get_squirrels patch.

        def it_returns_response_body_with_squirrels_json_data(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels):
            #Setup: no more setup necessary. all the fixtures solve the setup problem
            #note that mock_db_get_squirrels is passed in. Take that out of the parameters 
            #and run the test again - by passing the fixture - the patch gets done...
            #Do The thing:
            response = SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
            #assert that the write function was called with a json version of the text 'squirrel'
            # why that? look again at mock_db_get_squirrels
            response.wfile.write.assert_called_once_with(bytes(json.dumps(['squirrel']), "utf-8"))


    def describe_create_squirrels():

        def it_queries_db_to_create_squirrel_with_given_data_attributes(mocker, fake_create_squirrel_request, dummy_client, dummy_server):
            #setup.
            #patch createSquirrel
            mock_db_create_squirrel = mocker.patch.object(SquirrelDB,'createSquirrel',return_value=None)

            #do the thing.
            SquirrelServerHandler(fake_create_squirrel_request,dummy_client,dummy_server)

            #assert the thing was done.
            mock_db_create_squirrel.assert_called_once_with('Chippy','small')

    #actions
    def describe_actions():

        def describe_handleSquirrelsIndex():

            def it_calls_getSquirrels_on_the_db(fake_get_squirrels_request,dummy_client, dummy_server, mock_db_get_squirrels):
                SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                mock_db_get_squirrels.assert_called_once()
            
            def it_sends_a_200_response(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels, mock_response_methods):
                mock_send_response, _, _ = mock_response_methods
                SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(200)

        def describe_handleSquirrelsRetrieve():
            
            def it_calls_getSquirrel_with_the_id(mocker,fake_get_one_squirrel_request, dummy_client,dummy_server, mock_db_get_squirrel):
                SquirrelServerHandler(fake_get_one_squirrel_request, dummy_client, dummy_server)
                mock_db_get_squirrel.assert_called_once_with('1')

            def it_returns_200_if_squirrel_is_found(fake_get_one_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_response_methods):
                mock_send_response, _, _ = mock_response_methods
                SquirrelServerHandler(fake_get_one_squirrel_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(200)

            def it_returns_the_squirrel_data_in_the_body(fake_get_one_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel):
                response = SquirrelServerHandler(fake_get_one_squirrel_request, dummy_client, dummy_server)
                expected_data = {'id': 1, 'name': 'Squeaky', 'size': 'medium'}
                response.wfile.write.assert_called_once_with(bytes(json.dumps(expected_data), "utf-8"))

            def it_calls_handle_404_if_squirrel_not_found(mocker, fake_get_one_squirrel_request, dummy_client, dummy_server, mock_response_methods):
                mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
                mock_send_response, _, _ = mock_response_methods
                
                SquirrelServerHandler(fake_get_one_squirrel_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(404)

        def describe_handleSquirrelsCreate():

            def it_calls_createSquirrel_on_the_db(fake_create_squirrel_request, dummy_client, dummy_server, mock_db_create_squirrel):
                SquirrelServerHandler(fake_create_squirrel_request, dummy_client, dummy_server)
                mock_db_create_squirrel.assert_called_once_with('Chippy', 'small')

            def it_sends_a_201_response(fake_create_squirrel_request, dummy_client, dummy_server, mock_db_create_squirrel, mock_response_methods):
                mock_send_response, _, _ = mock_response_methods
                SquirrelServerHandler(fake_create_squirrel_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(201)

        def describe_handleSquirrelsUpdate():
            def when_squirrel_is_found():

                def it_calls_updateSquirrel_on_the_db(fake_update_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_update_squirrel):
                    SquirrelServerHandler(fake_update_squirrel_request, dummy_client, dummy_server)
                    mock_db_update_squirrel.assert_called_once_with('1', 'Squeaky', 'large')

                def it_sends_a_204_response(fake_update_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_update_squirrel, mock_response_methods):
                    mock_send_response, _, _ = mock_response_methods
                    SquirrelServerHandler(fake_update_squirrel_request, dummy_client, dummy_server)
                    mock_send_response.assert_called_once_with(204)

            def when_squirrel_is_not_found(mocker, fake_update_squirrel_request, dummy_client, dummy_server):
                
                def it_calls_handle404(mocker, mock_db_get_squirrel_not_found):
                    mock_handle_404 = mocker.patch.object(SquirrelServerHandler, 'handle404')
                    SquirrelServerHandler(fake_update_squirrel_request, dummy_client, dummy_server)
                    mock_handle_404.assert_called_once()

        def describe_handleSquirrelsDelete():
            
            def when_squirrel_is_found():
                
                def it_calls_deleteSquirrel_on_the_db(fake_delete_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_delete_squirrel):
                    SquirrelServerHandler(fake_delete_squirrel_request, dummy_client, dummy_server)
                    mock_db_delete_squirrel.assert_called_once_with('1')

                def it_sends_a_204_response(fake_delete_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_delete_squirrel, mock_response_methods):
                    mock_send_response, _, _ = mock_response_methods
                    SquirrelServerHandler(fake_delete_squirrel_request, dummy_client, dummy_server)
                    mock_send_response.assert_called_once_with(204)

            def when_squirrel_is_not_found(mocker, fake_delete_squirrel_request, dummy_client, dummy_server):
            
                def it_calls_handle404(mocker, mock_db_get_squirrel_not_found):
                    mock_handle_404 = mocker.patch.object(SquirrelServerHandler, 'handle404')
                    SquirrelServerHandler(fake_delete_squirrel_request, dummy_client, dummy_server)
                    mock_handle_404.assert_called_once()
            
        def describe_handle404():

            def it_sends_a_404_response(fake_not_found_request, dummy_client, dummy_server, mock_response_methods):
                mock_send_response, _, _ = mock_response_methods
                SquirrelServerHandler(fake_not_found_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(404)

            def it_sends_a_text_plain_content_type_header(fake_not_found_request, dummy_client, dummy_server, mock_response_methods):
                _, mock_send_header, _ = mock_response_methods
                SquirrelServerHandler(fake_not_found_request, dummy_client, dummy_server)
                mock_send_header.assert_called_once_with("Content-Type", "text/plain")
            
            def it_writes_a_not_found_message_to_the_body(fake_not_found_request, dummy_client, dummy_server, mock_response_methods):
                handler = SquirrelServerHandler(fake_not_found_request, dummy_client, dummy_server)
                handler.wfile.write.assert_called_once_with(bytes("404 Not Found", "utf-8"))
