from isoline.features import permissions_to_vector, InvalidAPKError, validate_apk_file
from isoline.schema import FEATURE_PERMISSIONS
import pytest

def test_vector_order_and_length():
    v = permissions_to_vector(["android.permission.INTERNET", "android.permission.SEND_SMS", "x.custom"])
    assert len(v) == len(FEATURE_PERMISSIONS)
    assert v[FEATURE_PERMISSIONS.index("android.permission.INTERNET")] == 1
    assert v[FEATURE_PERMISSIONS.index("android.permission.SEND_SMS")] == 1
    assert sum(v) == 2

def test_rejects_non_apk(tmp_path):
    f = tmp_path / "x.apk"; f.write_bytes(b"not a zip")
    with pytest.raises(InvalidAPKError):
        validate_apk_file(f)

def test_custom_feature_list_order():
    names = ["b.perm", "a.perm", "c.perm"]
    assert permissions_to_vector(["a.perm", "c.perm", "zzz"], names) == [0, 1, 1]
