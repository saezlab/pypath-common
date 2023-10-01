from pypath_common import _session

__all__ = ['TestSession']


class TestSession:
    def test_session_id(self):
        """
        This is a stupid test, just wanna have it here as a placeholder.
        """

        assert len(_session.Session.gen_session_id(10)) == 10
