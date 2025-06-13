import pytest
from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.gcp_helpers import poll_with_spinner
from vm_lifecycle.utils import gcphttperror
from googleapiclient.errors import HttpError


@pytest.fixture
def mock_gcp_clients(mocker):
    # Mock googleapiclient.discovery.build
    compute_mock = mocker.Mock()
    serviceusage_mock = mocker.Mock()

    # Patch 'build' to return different mocks depending on service name
    mocker.patch(
        "vm_lifecycle.compute_manager.build",
        side_effect=lambda service_name, *_args, **_kwargs: {
            "compute": compute_mock,
            "serviceusage": serviceusage_mock,
        }[service_name],
    )

    return compute_mock, serviceusage_mock


@pytest.fixture
def manager(mock_gcp_clients):
    compute_mock, serviceusage_mock = mock_gcp_clients
    return GCPComputeManager(project_id="test-project", zone="europe-west1-b")


def test_check_required_apis(manager, mock_gcp_clients):
    """Test that check_required_apis identifies enabled and missing APIs correctly."""
    _, serviceusage_mock = mock_gcp_clients

    list_mock = serviceusage_mock.services.return_value.list
    list_execute = list_mock.return_value.execute
    list_execute.return_value = {
        "services": [
            {"config": {"name": "compute.googleapis.com"}},
        ]
    }

    serviceusage_mock.services.return_value.list_next.return_value = None

    result = manager.check_required_apis()

    # Assert enabled/missing API sets
    assert "compute.googleapis.com" in result["enabled"]
    assert result["missing"] == []


def test_get_dangling_images(manager, mock_gcp_clients, mocker):
    """Test that get_dangling_images returns all but the latest image from a family."""
    compute_mock, _ = mock_gcp_clients

    latest_image = {"name": "img-3"}
    all_images = [
        {"name": "img-1", "family": "vm-image"},
        {"name": "img-2", "family": "vm-image"},
        {"name": "img-3", "family": "vm-image"},  # latest
    ]

    mocker.patch.object(
        manager, "get_latest_image_from_family", return_value=latest_image
    )
    mocker.patch.object(manager, "list_images", return_value=all_images)

    dangling = manager.get_dangling_images("vm-image")

    assert dangling == ["img-1", "img-2"]


def test_list_images_filters_family(manager, mock_gcp_clients):
    """Test that list_images filters images by family name if provided."""
    compute_mock, _ = mock_gcp_clients

    list_mock = compute_mock.images.return_value.list
    list_execute = list_mock.return_value.execute
    list_execute.return_value = {
        "items": [
            {"name": "img-a", "family": "f1"},
            {"name": "img-b", "family": "f2"},
            {"name": "img-c", "family": "f1"},
        ]
    }

    result = manager.list_images(family="f1")

    assert result == [
        {"name": "img-a", "family": "f1"},
        {"name": "img-c", "family": "f1"},
    ]


def test__list_regions(manager, mock_gcp_clients):
    """Test that _list_regions returns a list of region names from the API."""
    compute_mock, _ = mock_gcp_clients

    list_mock = compute_mock.regions.return_value.list
    list_execute = list_mock.return_value.execute
    list_execute.return_value = {
        "items": [
            {"name": "europe-west1"},
            {"name": "us-central1"},
        ]
    }

    result = manager._list_regions()

    assert result == ["europe-west1", "us-central1"]


def test__list_zones(manager, mock_gcp_clients):
    """Test that _list_zones returns only zones with status 'UP'."""
    compute_mock, _ = mock_gcp_clients

    zones_call = compute_mock.zones.return_value.list
    zones_execute = zones_call.return_value.execute

    zones_execute.side_effect = [
        {
            "items": [
                {"name": "europe-west1-b", "status": "UP"},
                {"name": "europe-west1-c", "status": "DOWN"},
            ]
        },
        {},
    ]

    compute_mock.zones.return_value.list_next.return_value = None

    result = manager._list_zones()

    assert result == ["europe-west1-b"]


def test_create_instance_basic(manager, mock_gcp_clients):
    """Test create_instance with default public image and no startup script."""
    compute_mock, _ = mock_gcp_clients

    insert_mock = compute_mock.instances.return_value.insert
    execute_mock = insert_mock.return_value.execute
    execute_mock.return_value = {"status": "PENDING"}

    result = manager.create_instance(
        instance_name="test-vm",
        machine_type="e2-standard-2",
        disk_size=50,
        instance_user="user1",
    )

    # Call should succeed with minimal config
    assert result == {"status": "PENDING"}
    assert insert_mock.called

    args, kwargs = insert_mock.call_args
    config = kwargs["body"]
    assert config["name"] == "test-vm"
    assert "startup-script" not in config.get("metadata", {}).get("items", [{}])[0].get(
        "key", ""
    )


def test_create_instance_with_custom_image(manager, mock_gcp_clients):
    """Test create_instance uses a custom image path when provided."""
    compute_mock, _ = mock_gcp_clients

    insert_mock = compute_mock.instances.return_value.insert
    insert_mock.return_value.execute.return_value = {"status": "PENDING"}

    result = manager.create_instance(
        instance_name="test-vm",
        machine_type="e2-standard-2",
        disk_size=50,
        instance_user="user1",
        custom_image_name="my-custom-image",
    )

    assert result["status"] == "PENDING"
    config = insert_mock.call_args.kwargs["body"]
    assert "my-custom-image" in config["disks"][0]["initializeParams"]["sourceImage"]


def test_create_instance_with_ansible_script(
    manager, mock_gcp_clients, tmp_path, mocker
):
    """Test create_instance loads ansible startup script and formats it correctly."""
    compute_mock, _ = mock_gcp_clients

    # Create a temporary ansible script file
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    script_path = script_dir / "startup_ansible.sh"
    script_path.write_text("echo Hello {instance_user}")

    # Patch the internal path reference in the module
    mocker.patch(
        "vm_lifecycle.compute_manager.Path",
        lambda *args, **kwargs: tmp_path / "scripts",
    )

    insert_mock = compute_mock.instances.return_value.insert
    insert_mock.return_value.execute.return_value = {"status": "PENDING"}

    result = manager.create_instance(
        instance_name="test-vm",
        machine_type="e2-standard-2",
        disk_size=50,
        instance_user="goku",
        startup_script_type="ansible",
    )

    assert result["status"] == "PENDING"

    metadata_items = insert_mock.call_args.kwargs["body"]["metadata"]["items"]
    assert any("goku" in item["value"] for item in metadata_items)


def test_wait_for_operation_success_zone(manager, mock_gcp_clients, mocker):
    """Test wait_for_operation handles successful zone-scoped operations."""
    compute_mock, _ = mock_gcp_clients

    # Mock the zone operation to return 'DONE' without error
    op_get = compute_mock.zoneOperations.return_value.get
    op_get.return_value.execute.return_value = {"status": "DONE"}

    gen = manager.wait_for_operation(
        operation_name="op-123",
        scope="zone",
        zone="europe-west1-b",
        timeout=10,
        poll_interval=1,
    )

    while True:
        try:
            next(gen)
        except StopIteration as stop:
            result = stop.value
            break
    assert result["success"] is True
    assert result["operation"]["status"] == "DONE"


def test_wait_for_operation_failure_global(manager, mock_gcp_clients, mocker):
    """Test wait_for_operation returns failure if operation has error."""
    compute_mock, _ = mock_gcp_clients

    op_get = compute_mock.globalOperations.return_value.get
    op_get.return_value.execute.return_value = {
        "status": "DONE",
        "error": {"code": 400, "message": "bad request"},
    }

    gen = manager.wait_for_operation(
        operation_name="op-456",
        scope="global",
        timeout=10,
        poll_interval=1,
    )

    while True:
        try:
            next(gen)
        except StopIteration as stop:
            result = stop.value
            break

    assert result["success"] is False
    assert "error" in result
    assert result["operation"]["status"] == "DONE"


def test_wait_for_operation_timeout(manager, mock_gcp_clients, mocker):
    """Test wait_for_operation raises TimeoutError if operation exceeds timeout."""
    compute_mock, _ = mock_gcp_clients

    # Always return RUNNING
    op_get = compute_mock.zoneOperations.return_value.get
    op_get.return_value.execute.return_value = {"status": "RUNNING"}

    gen = manager.wait_for_operation(
        operation_name="op-789",
        scope="zone",
        zone="europe-west1-b",
        timeout=1,
        poll_interval=0.1,
    )

    with pytest.raises(TimeoutError):
        while True:
            next(gen)


def test_poll_with_spinner_success(mocker):
    """Test poll_with_spinner exits cleanly when operation reports success."""
    mock_generator = mocker.Mock()
    mock_generator.return_value = iter(
        ["RUNNING", {"success": True, "operation": {"status": "DONE"}}]
    )

    mock_manager = mocker.Mock()
    mock_manager.wait_for_operation = mock_generator

    result = poll_with_spinner(
        compute_manager=mock_manager,
        op_name="op-123",
        text="Testing spinner...",
        scope="zone",
        zone="europe-west1-b",
    )

    assert result["success"] is True
    assert result["operation"]["status"] == "DONE"


def test_poll_with_spinner_failure(mocker):
    """Test poll_with_spinner handles failed operation and returns error dict."""

    def failing_generator(*args, **kwargs):
        yield "RUNNING"
        yield {"success": False, "error": {"code": 500, "message": "failed"}}

    mock_manager = mocker.Mock()
    mock_manager.wait_for_operation = lambda *a, **k: failing_generator()

    result = poll_with_spinner(
        compute_manager=mock_manager,
        op_name="fail-op",
        text="Expecting failure...",
        scope="zone",
        zone="europe-west1-b",
    )

    assert result["success"] is False
    assert "error" in result


def test_wait_for_operation_invalid_scope_raises(manager):
    """Should raise ValueError if scope is not 'zone' or 'global'."""
    with pytest.raises(ValueError, match="Unsupported operation scope"):
        gen = manager.wait_for_operation(operation_name="abc", scope="invalid")
        next(gen)


def test_poll_with_spinner_generator_runtime_error(mocker):
    """Should return error dict if generator raises RuntimeError."""

    def broken_generator(*args, **kwargs):
        yield "RUNNING"
        raise RuntimeError("something failed")

    mock_manager = mocker.Mock()
    mock_manager.wait_for_operation = lambda *a, **k: broken_generator()

    result = poll_with_spinner(
        compute_manager=mock_manager,
        op_name="fail-op",
        text="Testing failure",
        scope="zone",
        zone="europe-west1-b",
    )

    assert result["success"] is False
    assert "something failed" in result["error"]


def test_poll_with_spinner_generator_returns_failure_dict(mocker):
    """Should return failure dict if generator ends with success=False."""

    def failing_generator(*args, **kwargs):
        yield "RUNNING"
        return {"success": False, "error": {"msg": "failed operation"}}

    mock_manager = mocker.Mock()
    mock_manager.wait_for_operation = lambda *a, **k: failing_generator()

    result = poll_with_spinner(
        compute_manager=mock_manager,
        op_name="fail-op",
        text="Failure return test",
        scope="zone",
        zone="europe-west1-b",
    )

    assert result["success"] is False


def test_gcphttperror_decorator_prints_and_exits(mocker):
    """Decorator should catch HttpError, print message, and exit with code 1."""
    mock_sys_exit = mocker.patch("vm_lifecycle.utils.sys.exit")

    fake_resp = mocker.Mock(status=403)

    class FakeHttpError(HttpError):
        def __init__(self):
            super().__init__(resp=fake_resp, content=b"forbidden")

    @gcphttperror()
    def error_function():
        raise FakeHttpError()

    error_function()

    mock_sys_exit.assert_called_once_with(1)


def test_list_images_returns_empty_if_no_items(manager, mock_gcp_clients):
    """Should return empty list if no images are found."""
    compute_mock, _ = mock_gcp_clients
    compute_mock.images.return_value.list.return_value.execute.return_value = {}

    result = manager.list_images()
    assert result == []


def test_get_instance_status_not_found_raises(manager, mock_gcp_clients):
    """Should raise ValueError if instance is not found in list."""
    compute_mock, _ = mock_gcp_clients

    compute_mock.instances.return_value.list.return_value.execute.return_value = {
        "items": []
    }

    with pytest.raises(ValueError, match="not found in zone"):
        manager.get_instance_status("nonexistent", zone="europe-west1-b")


def test_get_dangling_images_empty_family(manager, mocker):
    """Should return empty list when only the latest image exists."""
    latest_image = {"name": "img-1"}
    all_images = [{"name": "img-1", "family": "f1"}]

    mocker.patch.object(
        manager, "get_latest_image_from_family", return_value=latest_image
    )
    mocker.patch.object(manager, "list_images", return_value=all_images)

    result = manager.get_dangling_images("f1")
    assert result == []


def test_create_image_from_instance_uses_boot_disk_correctly(manager, mock_gcp_clients):
    """Should parse and use boot disk name from instance config."""
    compute_mock, _ = mock_gcp_clients

    compute_mock.instances.return_value.get.return_value.execute.return_value = {
        "disks": [{"boot": True, "source": "projects/x/zones/y/disks/my-disk"}]
    }

    insert_mock = compute_mock.images.return_value.insert
    insert_mock.return_value.execute.return_value = {"status": "PENDING"}

    result = manager.create_image_from_instance(
        instance_name="vm1",
        image_name="my-image",
        family="my-family",
        zone="europe-west1-b",
    )

    assert result["status"] == "PENDING"
    call_args = insert_mock.call_args.kwargs["body"]
    assert "sourceDisk" in call_args
    assert "my-disk" in call_args["sourceDisk"]
