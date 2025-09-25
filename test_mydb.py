import os
import pytest
from mydb import MyDB
from unittest.mock import call

todo = pytest.mark.skip(reason='todo: pending spec')

def describe_MyDB():

    @pytest.fixture(autouse=True, scope="session")
    def verify_filesystem_is_not_touched():
        yield
        assert not os.path.isfile("mydatabase.db")

    def describe_init():
        def it_assigns_fname_attribute(mocker):
            mocker.patch("os.path.isfile", return_value=True)
            db = MyDB("mydatabase.db")
            assert db.fname == "mydatabase.db"

        def it_creates_empty_database_if_it_does_not_exist(mocker):
            # set up stubs & mocks first
            mock_isfile = mocker.patch("os.path.isfile", return_value=False)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_dump = mocker.patch("pickle.dump")

            # execute on the test subject
            db = MyDB("mydatabase.db")

            # assert what happened
            mock_isfile.assert_called_once_with("mydatabase.db")
            mock_open.assert_called_once_with("mydatabase.db", "wb")
            mock_dump.assert_called_once_with([], mock_open.return_value)

        
        def it_does_not_create_database_if_it_already_exists(mocker):
            mock_isfile = mocker.patch("os.path.isfile",return_value=True)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_dump = mocker.patch("pickle.dump")

            db = MyDB("mydatabase.db")
            mock_isfile.assert_called_once_with("mydatabase.db")
            mock_open.assert_not_called()
            mock_dump.assert_not_called()
            
    
    def describe_loadStrings():
        
        def it_loads_an_array_from_a_file_and_returns_it(mocker):
            mock_isfile = mocker.patch("os.path.isfile",return_value=True)            
            mock_open = mocker.patch("builtins.open",mocker.mock_open())
            mock_load = mocker.patch("pickle.load",return_value=["hello","world"])
            db = MyDB("mydatabase.db")
            result = db.loadStrings()
            mock_open.assert_called_once_with("mydatabase.db","rb")
            mock_load.assert_called_once_with(mock_open.return_value)
            assert result == ["hello","world"]

    def describe_saveStrings():
        def it_saves_the_given_array_to_a_file(mocker):
            mock_isfile = mocker.patch("os.path.isfile",return_value=True)            
            mock_open = mocker.patch("builtins.open",mocker.mock_open())
            mock_dump = mocker.patch("pickle.dump")
            db = MyDB("mydatabase.db")
            test_data = ["hello","world"]
            db.saveStrings(test_data)
            mock_open.assert_called_once_with("mydatabase.db","wb")
            mock_dump.assert_called_once_with(test_data,mock_open.return_value)

            
    
    def describe_saveString():
        def it_appends_string_element_to_existing_database(mocker):
            mock_isfile = mocker.patch("os.path.isfile",return_value=True)            
            db = MyDB("mydatabase.db")
            mocker.patch.object(db,'loadStrings', return_value=["hello","world"])
            mock_save = mocker.patch.object(db,'saveStrings')
            db.saveString("new_string")
            db.loadStrings.assert_called_once()
            mock_save.assert_called_once_with(["hello","world","new_string"])
