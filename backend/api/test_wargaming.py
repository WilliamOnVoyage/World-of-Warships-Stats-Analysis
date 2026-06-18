import pytest
from httpx import Response
from api.wargaming import WargamingAPIClient

@pytest.fixture
def api_client():
    return WargamingAPIClient(application_id="test_app_id")

@pytest.mark.asyncio
async def test_get_account_id_success(api_client, mocker):
    # Mock the internal _make_request to return successful response
    mock_request = mocker.patch.object(api_client, "_make_request", return_value=[{"account_id": 12345, "nickname": "TestPlayer"}])
    
    account_id = await api_client.get_account_id("TestPlayer")
    
    assert account_id == 12345
    mock_request.assert_called_once_with("/wows/account/list/", {"search": "TestPlayer", "type": "exact"})

@pytest.mark.asyncio
async def test_get_account_id_not_found(api_client, mocker):
    mock_request = mocker.patch.object(api_client, "_make_request", return_value=[])
    
    account_id = await api_client.get_account_id("UnknownPlayer")
    
    assert account_id is None
    
@pytest.mark.asyncio
async def test_get_player_info(api_client, mocker):
    mock_response = {
        "12345": {
            "statistics": {
                "battles": 100,
                "pvp": {"wins": 55}
            }
        }
    }
    mock_request = mocker.patch.object(api_client, "_make_request", return_value=mock_response)
    
    info = await api_client.get_player_info([12345])
    
    assert info == mock_response
    mock_request.assert_called_once_with("/wows/account/info/", {"account_id": "12345"})

@pytest.mark.asyncio
async def test_make_request_error(api_client, mocker):
    # Test that the httpx error is properly raised when status is not ok
    mock_client = mocker.patch.object(api_client.client, "get")
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "error", "error": {"message": "INVALID_APPLICATION_ID"}}
    mock_client.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        await api_client._make_request("/test", {})
    
    assert "Wargaming API Error" in str(exc_info.value)
