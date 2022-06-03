import pypath_common


class TestSession:
    def test_session_id(self):
        """
        This is a stupid test, just wanna have it here as a placeholder.
        """

        assert len(pypath_common.Session.gen_session_id(10)) == 10
